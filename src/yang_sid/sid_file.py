# SPDX-FileCopyrightText: CZ.NIC z.s.p.o.
#
# SPDX-License-Identifier: LGPL-3.0-or-later

import json
import re
import yang_sid
import yangson.instance
import yangson.typealiases

from typing import Iterator, Iterable, ClassVar, Union, TYPE_CHECKING, cast
from enum import Enum
from pathlib import Path
from dataclasses import dataclass, field


from yang_library import *

from .types import SID
from ._sid_file_types import *

if TYPE_CHECKING:
    from .schema_data import ModuleData

# TODO implement checks of validity / consistency

class SidFileStatus(Enum):
    UNPUBLISHED = "unpublished"
    PUBLISHED = "published"

class ItemStatus(Enum):
    STABLE = "stable"
    UNSTABLE = "unstable"
    OBSOLETE = "obsolete"

class ItemNamespace(Enum):
    MODULE = "module"
    IDENTITY = "identity"
    FEATURE = "feature"
    DATA = "data"

@dataclass
class ModuleDependency:
    name: yangson.typealiases.YangIdentifier
    revision: yangson.typealiases.RevisionDate

@dataclass
class AssignmentRange:
    entry_point: SID
    size: int

@dataclass
class ItemAssignment:
    # TODO wouldn't be SidFileItem more readable?
    namespace: ItemNamespace
    identifier: Union[str, yangson.typealiases.YangIdentifier]
    sid: SID
    status: ItemStatus = ItemStatus.STABLE

@dataclass
class SidFile:
    module: yangson.typealiases.YangIdentifier
    revision: Optional[yangson.typealiases.RevisionDate]
    version: int
    status: SidFileStatus
    item: dict[SID, ItemAssignment]
    assignment_range: list[AssignmentRange]
    dependency_revision: dict[yangson.typealiases.YangIdentifier, ModuleDependency] # ModuleName -> ModuleId(name, revision)
    description: str = ""

@dataclass
class SidRepository:
    files: dict[str, SidFile] = field(default_factory=lambda: dict())
    global_mapping: dict[SID, ItemAssignment] = field(default_factory=lambda: dict())

    def __iter__(self) -> Iterator[Any]:
        return iter(self.files)

    def __contains__(self, module: Any) -> bool:
        return module in self.files

    def load_sid_file(self, data: yangson.schemadata.SchemaData, module: yangson.schemadata.ModuleData) -> None:
        pass

    def check_sid_file(self, data: yangson.schemadata.SchemaData, sid_file: SidFile) -> bool:
        return False

def _get_list_raw(inst: yangson.instance.InstanceNode, name: str) -> yangson.typealiases.RawList:
    try:
        lst = inst[name]
        return cast(yangson.typealiases.RawList, lst.raw_value())
    except yangson.exceptions.NonexistentInstance:
        return []
    except KeyError:
        return []

def _get_mod_rev(instance: yangson.instance.InstanceNode) -> Optional[str]:
    try:
        return cast(str, instance["module-revision"].value)
    except yangson.exceptions.NonexistentInstance:
        return None

class SidFileLoader:
    # same as uytc.core.yang_library.YangLibrary RFC_MODEL_DIR
    RFC_MODEL_DIR = Path(yang_sid.__file__).parent / "yang_modules"
    SID_FILE_MODEL: ClassVar[yangson.datamodel.DataModel] = yangson.datamodel.DataModel.from_file(
        RFC_MODEL_DIR / 'ietf-sid-file-library.json', mod_path = (RFC_MODEL_DIR, '.')
        )

    #PATTERN_NO_REV: ClassVar[str] = "^{module.name}\\.sid$"
    #PATTERN_WITH_REV: ClassVar[str] = "^{module.name}(@{module.revision})?\\.sid$"
    PATTERN_NO_REV_EXT: ClassVar[str] = "^{name}(\\.[0-9]+)?\\.sid$"
    PATTERN_WITH_REV_EXT: ClassVar[str] = "^{name}(@{revision})?(\\.[0-9]+)?\\.sid$"

    @classmethod
    def load_sid_file(cls, module: yangson.schemadata.ModuleData, sid_path: Iterable[str]) -> SidFile:
        filename = cls._find_sid_file(module, sid_path, ext_filename)
        if not filename:
            raise ValueError(f"SID File for YANG module {module.yang_id[0]} was not found.")

        sid_file = cls.parse_sid_file(filename)
        # TODO module revision None/""
        if sid_file.module != module.name or sid_file.revision != module.revision:
            raise ValueError("Wrong SID File for a given module")
        return sid_file

    @classmethod
    def find_sid_file(cls, module: yangson.schemadata.ModuleData, sid_path: Iterable[str]) -> Optional[Path]:
        pattern_no_rev = re.compile(cls.PATTERN_NO_REV_EXT.format(name=module.yang_id[0]))
        pattern_with_rev = re.compile(cls.PATTERN_WITH_REV_EXT.format(name=module.yang_id[0], revision=module.yang_id[1]))

        for pattern in (pattern_with_rev, pattern_no_rev):
            for path_str in sid_path:
                path = Path(path_str)
                # TODO check behaviour of links
                if path.is_dir():
                    for file in path.iterdir():
                        if pattern.match(file.name):
                            return path / file
                elif path.is_file():
                    if pattern.match(path.name):
                        return path
        return None

    @classmethod
    def parse_sid_file(cls, file: str) -> SidFile:
        with open(file, mode='r', encoding="utf-8") as fd:
            raw = json.load(fd)

        sid_file_raw: yangson.instance.InstanceNode = SidFileLoader.SID_FILE_MODEL.from_raw(raw)
        sid_file_raw = sid_file_raw.add_defaults()
        sid_file_raw.validate()

        return cls._process_data(sid_file_raw)

    @staticmethod
    def _process_data(sid_file: yangson.instance.InstanceNode) -> SidFile:
        # TODO rework sid_file_cont (it is InstanceNode, not raw dict)
        sid_file_cont = cast(SidFileDict, sid_file["ietf-sid-file:sid-file"]) # Sid file content
        module = sid_file_cont["module-name"].value
        version = sid_file_cont["sid-file-version"].value
        revision = _get_mod_rev(sid_file_cont)
        status = SidFileStatus(sid_file_cont["sid-file-status"].value)
        description = sid_file_cont["description"].value if "description" in sid_file_cont else ""

        # yangson uses empty string for revisionless modules
        main_mod_id: yangson.typealiases.ModuleId = (module, revision
                if revision is not None else "")

        dependencies: dict[yangson.typealiases.YangIdentifier, ModuleData] = {}
        for dep_dict in cast(list[DependencyRevision], _get_list_raw(sid_file_cont, "dependency-revision")):
            # the dep's attribute "module-revision" is required to be present by YANG (and checked by yangson)
            # TODO module-revision ""/None
            dep = ModuleDependency(dep_dict["module-name"], dep_dict["module-revision"])
            dependencies[dep.name] = dep

        all_ranges: list[AssignmentRange] = []
        for asgn_range in cast(list[AssignmentRangeDict], _get_list_raw(sid_file_cont, "assignment-range")):
            all_ranges.append(AssignmentRange(SID(asgn_range["entry-point"]), asgn_range["size"]))

        all_ranges.sort(key=lambda asgn_range: asgn_range.entry_point)

        for i in range(1, len(all_ranges)):
            prev_range = all_ranges[i - 1]
            curr_range = all_ranges[i]

            if prev_range.entry_point + prev_range.size >= curr_range.entry_point:
                raise ValueError("Overlapping range assignment")

        sid_file_entries: dict[SID, ItemAssignment] = {} # TODO rename ItemAssignment
        for item in sid_file_cont["item"]:
            item_status = ItemStatus(item["status"].value)
            namespace = ItemNamespace(item["namespace"].value)
            item_id = item["identifier"].value
            sid = SID(item["sid"].value)

            sid_file_entries[sid] = ItemAssignment(namespace, item_id, sid, item_status)

        return SidFile(module, revision, version, status,
                       item=sid_file_entries, assignment_range=all_ranges,
                       dependency_revision=dependencies, description=description)

