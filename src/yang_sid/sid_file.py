# SPDX-FileCopyrightText: CZ.NIC z.s.p.o.
#
# SPDX-License-Identifier: LGPL-3.0-or-later

import yang_sid
import yangson.typealiases

from typing import Iterator, Iterable, ClassVar, TYPE_CHECKING
from enum import Enum
from pathlib import Path
from dataclasses import dataclass, field

from yang_library import *

from .types import SID
from ._sid_file_types import *
from .schema import SchemaNode

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
    identifier: str
    sid: SID
    status: ItemStatus = ItemStatus.STABLE

@dataclass
class SidFile:
    module: yangson.typealiases.YangIdentifier
    revision: Optional[yangson.typealiases.RevisionDate]
    version: int
    status: SidFileStatus
    item: dict[SID, ItemAssignment]
    dependency_revision: list[ModuleDependency]

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

    print("ietf-sid-file-library.json LOADED")

    PATTERN_NO_REV: ClassVar[str] = "^{module.name}\\.sid$"
    PATTERN_WITH_REV: ClassVar[str] = "^{module.name}(@{module.revision})?\\.sid$"
    PATTERN_NO_REV_EXT: ClassVar[str] = "^{module.name}(\\.[0-9]+)?\\.sid$"
    PATTERN_WITH_REV_EXT: ClassVar[str] = "^{module.name}(@{module.revision})?(\\.[0-9]+)?\\.sid$"

    @classmethod
    def load_sid_file(cls, module: yangson.schemadata.ModuleData, sid_path: Iterable[str]) -> Optional[SidFile]:
        filename = cls._find_sid_file(module, sid_path, ext_filename)
        if not filename:
            return None

        return cls.parse_sid_file(module, filename)

    @classmethod
    def find_sid_file(cls, module: yangson.schemadata.ModuleData, sid_path: Iterable[str]) -> Optional[Path]:
        pattern_no_rev = re.compile(cls.PATTERN_NO_REV_EXT.format(module=module))
        pattern_with_rev = re.compile(cls.PATTERN_WITH_REV_EXT.format(module=module))

        for pattern in (pattern_with_rev, pattern_no_rev):
            for path_str in sid_path:
                path = Path(path_str)
                # TODO check behaviour of links
                if path.is_dir:
                    for file in os.listdir(path):
                        if pattern.match(file):
                            return path / file
                elif path.is_file:
                    if pattern.match(path):
                        return path
        return None
 
    @classmethod
    def parse_sid_file(cls, module: yangson.schemadata.ModuleData, filename: str) -> Optional[SidFile]:
        with open(filename, "r", encoding="utf-8") as file:
            sid_file = json.load(file)

    @staticmethod
    def load_sid_files2(schema_ctx: "SchemaContext") -> None:
        patterns = OrderedDict()

        for mod_set in schema_ctx.schema.module_set.values():
            for group in (mod_set.module.values(), mod_set.import_only_module.values()):
                for mod in group:
                    if mod.revision:
                        pat = f"^{mod.name}(@{mod.revision})?\\.sid$"
                    else:
                        pat = f"^{mod.name}\\.sid$"

                    # TODO remove this hack by: a) making the result of DataModel schema a frozen hierarchy
                    # b) creating builders with lists for simpler parsing / handling
                    if isinstance(mod, Module):
                        mod.location = tuple(mod.location)
                        mod.submodule = FrozenOrderedDict(mod.submodule)

                    if isinstance(mod, ImplementModule):
                        mod.feature = tuple(mod.feature)
                        mod.deviation = FrozenOrderedDict(mod.deviation)

                    patterns[mod] = re.compile(pat)

        matches = {}
        for dir in schema_ctx._parent.sid_path:
            if not os.path.exists(dir):
                continue

            if os.path.isdir(dir):
                all_files = filter(lambda f: os.path.isfile(f),
                                   os.listdir(dir))

                for file in all_files:
                    for (mod, pat) in patterns.items():
                        match = pat.match(file)
                        if match:
                            (matches.setdefault(mod, [])
                                .append((match, dir)))

            #elif os.path.isfile(dir):
            #    for (mod, pat) in patterns.items():
            #        match = pat.match(dir)
            #        if match:
            #            (matches.setdefault(mod, [])
            #                .append((match, dir))

        for (mod, matches) in matches.items():
            if mod.revision:
                match_iter = itertools.chain(
                        filter(lambda m: m[0].groups()[0] is not None, matches),
                        filter(lambda m: m[0].groups()[0] is None, matches))
            else:
                match_iter = matches

            for (match, dir) in match_iter:
                filename = os.path.join(dir, match.string)
                SidFileLoader.parse_sid_file(schema_ctx._sid_repository,
                                             mod,
                                             filename,
                                             schema_ctx)

        # inject SIDs from choice cases children to parent of choice
        root = schema_ctx._schema_node
        for choice_node in SchemaTreeIterator(root):
            if not SchemaNode.is_choice(choice_node):
                continue
            for case_node in choice_node.children.values():
                for child in case_node.children.values():
                    choice_node.sid_children[child.sid] = child
                    choice_node.parent.sid_children[child.sid] = child

    # TODO rename to load/loads to follow similar naming convesion as YangLibrary?
    @staticmethod
    def parse_sid_file2(repository: SidRepository, module: Module, file: str, schema_ctx: "SchemaContext") -> None:
        schema = schema_ctx.schema
        schema_data = schema_ctx._ys_data_model.schema_data

        with open(file, mode='r') as fd:
            raw = json.load(fd)

        sid_file_raw: yangson.instance.InstanceNode = SidFileLoader.SID_FILE_MODEL.from_raw(raw)
        sid_file_raw = sid_file_raw.add_defaults()
        sid_file_raw.validate()

        sid_file = SidFileLoader._process_data(sid_file_raw, schema_ctx, schema_data)

        repository.files[module] = sid_file
        # TODO check that items do not collide, checked by yangson; not required
        repository.global_mapping.update(sid_file.item)

        root = schema_ctx._schema_node
        for item in sid_file.item.values():
            if item.namespace != ItemNamespace.DATA:
                continue

            inst_route = yangson.instance.InstanceIdParser(item.identifier).parse()
            sch_route = inst_route.as_schema_route()
            node = schema_ctx._schema_node.get_schema_descendant(sch_route)

            if not SchemaNode.is_action(node):
                continue

            # XXX finish the thought

    @staticmethod
    def _check_revisions(model: YangLibrary, file: SidFile) -> None:
        pass

    @staticmethod
    def _process_data(sid_file: yangson.instance.InstanceNode, schema_ctx: "SchemaContext", schema_data: yangson.schemadata.SchemaData) -> SidFile:
        schema = schema_ctx.schema

        # TODO rework sid_file_cont (it is InstanceNode, not raw dict)
        sid_file_cont = cast(SidFileDict, sid_file["ietf-sid-file:sid-file"]) # Sid file content
        module = sid_file_cont["module-name"].value
        version = sid_file_cont["sid-file-version"].value
        revision = _get_mod_rev(sid_file_cont)
        status = SidFileStatus(sid_file_cont["sid-file-status"].value)

        # yangson uses empty string for revisionless modules
        main_mod_id: yangson.typealiases.ModuleId = (module, revision
                if revision is not None else "")
        main_mod_data = sid_schema_data.modules.get(main_mod_id)

        if main_mod_data is None:
            raise ValueError("Missing module") # TODO more helpful message - is the module known? is there only a revision mismatch?

        dependencies: dict[yangson.typealiases.YangIdentifier, ModuleData] = {}
        for dep in cast(list[DependencyRevision], get_list_raw(sid_file_cont, "dependency-revision")):
            # the dep's attribute "module-revision" is required to be present by YANG (and checked by yangson)
            mod_id: yangson.typealiases.ModuleId = (dep["module-name"], dep["module-revision"])
            mod_data = sid_schema_data.modules.get(mod_id)
            if mod_data is not None:
                dependencies[dep["module-name"]] = mod_data
            else:
                raise ValueError("Missing module") # TODO message

        all_ranges: list[AssignmentRange] = []
        for asgn_range in cast(list[AssignmentRangeDict], get_list_raw(sid_file_cont, "assignment-range")):
            all_ranges.append(AssignmentRange(Sid(asgn_range["entry-point"]), asgn_range["size"]))

        all_ranges.sort(key=lambda asgn_range: asgn_range.entry_point)

        for i in range(1, len(all_ranges)):
            prev_range = all_ranges[i - 1]
            curr_range = all_ranges[i]

            # the yangson did validate that entry points are unique (it is a YANG defined contraint)

            if prev_range.entry_point + prev_range.size >= curr_range.entry_point:
                raise ValueError("Overlapping range assignment")

        root = schema_ctx._schema_node
        sid_file_entries: dict[SID, ItemAssignment] = {} # TODO rename ItemAssignment
        for item in sid_file_cont["item"]:
            item_status = ItemStatus(item["status"].value)
            namespace = ItemNamespace(item["namespace"].value)
            item_id = item["identifier"].value
            sid = SID(item["sid"].value)

            if namespace == ItemNamespace.MODULE:
                assert item_id == module
                main_mod_data.sid = sid
            elif namespace == ItemNamespace.IDENTITY:
                qual_name: QualName = (item_id, module)
                identity = sid_schema_data.identity_adjs.get(qual_name)
                if identity is not None:
                    identity.sid = sid
                else:
                    raise ValueError("Unknown identity")
            elif namespace == ItemNamespace.FEATURE:
                if item_id not in main_mod_data.all_features:
                    raise ValueError("Unknown feature")

                main_mod_data.sid_features[sid] = item_id
            elif namespace == ItemNamespace.DATA:
                route = schema_ctx._ys_data_model.schema_data.path2route(item_id)
                node = root.get_schema_descendant(route)
                if not node:
                    raise ValueError(f"Schema node on path {item_id} not found")
                node.sid = sid
                if node.parent:
                    node.parent.sid_children[sid] = node

                root.global_sid_mapping[sid] = node
            else:
                assert_never(namespace)

            sid_file_entries[sid] = ItemAssignment(namespace, item_id, sid, item_status)

        # TODO rewrite to remove the assert
        assert isinstance(root, SchemaTreeNode)
        return SidFile("module", None, 1, SidFileStatus.UNPUBLISHED,
                       item=sid_file_entries, dependency_revision=dependencies)

    @staticmethod
    def _fill_schema_tree(file: SidFile, root: SchemaNode) -> None:
        pass

