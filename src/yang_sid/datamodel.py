# SPDX-FileCopyrightText: CZ.NIC z.s.p.o.
#
# SPDX-License-Identifier: LGPL-3.0-or-later

import copy
import json

import yangson.datamodel
import yangson.schemadata
import yangson.schemanode

from .schemanode import SchemaTreeFactory, SchemaTreeNode
from .schemadata import SchemaDataFactory, ModuleData, SchemaData
from .sid_file import SidFile

from pathlib import Path
from collections.abc import Iterable
from typing import Optional, Union


"""Basic access to the yang_sid library.

This module implements the following class:

* DataModel: User-level entry point to yang-sid library with YANG-SID support.
"""

class DataModel(yangson.datamodel.DataModel):
    """User-level entry point to yang-sid library with YANG-SID support."""

    schema_data: SchemaData
    schema: SchemaTreeNode

    def __init__(self, yltxt: str, mod_path: tuple[str] = (".",),
                 description: Optional[str] = None,
                 data_factory: Optional[yangson.schemadata.SchemaDataFactory] = None,
                 tree_factory: Optional[yangson.schemanode.SchemaTreeFactory] = None) -> None:
        """Initialize the class instance. Factories defaults to classes with support of YANG-SID.

        Args:
            yltxt: JSON text with YANG library data.
            mod_path: Tuple of directories where to look for YANG modules.
            description: Optional description of the data model.
            data_factory: Factory for getting SchemaData instance with SID support.
            tree_factory: Factory for getting SchemaTreeNode instance wit SID support.

        Raises:
            BadYangLibraryData: If YANG library data is invalid.
            FeaturePrerequisiteError: If a pre-requisite feature isn't
                supported.
            MultipleImplementedRevisions: If multiple revisions of an
                implemented module are listed in YANG library.
            ModuleNotFound: If a YANG module wasn't found in any of the
                directories specified in `mod_path`.
        """

        if data_factory is None:
            data_factory = SchemaDataFactory()

        if tree_factory is None:
            tree_factory = SchemaTreeFactory()

        super().__init__(yltxt, mod_path, description, data_factory, tree_factory)
        if not isinstance(self.schema_data, SchemaData):
            raise TypeError("yang_sid.DataModel requires SchemaData from yang_sid package.")
        if not isinstance(self.schema, SchemaTreeNode):
            raise TypeError("yang_sid.DataModel requires SchemaTreeNode from yang_sid package.")

        self._build_complete_model(data_factory, tree_factory)

    def set_sid_path(self, sid_path: Iterable[str]) -> None:
        """Set search path for SID Files."""

        self.complete_model.schema_data.set_sid_path(sid_path)
        self.schema_data.set_sid_path(sid_path)

    def load_sid_file(self, file: Union[str, Path]) -> SidFile:
        """Load a SID File from given path.

        Args:
            file: Path to file to be loaded.
        """

        file = Path(file)
        parsed_file = self.schema_data.load_sid_file(file)
        self.complete_model.schema_data.apply_sid_file(parsed_file)
        self.complete_model.schema.apply_sid_file(parsed_file)

        # TODO implement more efficient algoritm that copy only loaded sids, not all of them
        self.schema_data.copy_sids_from(self.complete_model.schema_data)
        self.schema.copy_sids_from(self.complete_model.schema, self.schema_data)
        return parsed_file

    def load_all_module_sids(self) -> None:
        """Search and load all SID Files on the SID path for YANG modules from loaded library."""

        complete = self.complete_model


        for mod_id in complete.schema_data.modules:
            mod = complete.schema_data.modules[mod_id]

            self.load_module_sids(mod)

    def load_all_sid_files(self) -> None:
        """Search and load all SID Files on the SID path for YANG modules from loaded library.

        Alias to load_all_modules_sids()
        """

        self.load_all_module_sids()

    def load_module_sids(self, mod_data: ModuleData) -> bool:
        """Search and load a SID File for given module.

        Args:
            mod_data: Single YANG modules to be loaded SIDs.
        """

        file = self.schema_data.find_sid_file(mod_data)
        if file is None:
            return False
        parsed = self.load_sid_file(file)
        # We ignore 'dependency_revision' list intentionally
        return True

    def apply_sid_file(self, sid_file: SidFile) -> None:
        """Use SID item assignments from loaded and parsed SID File on the schema tree as well as the schema data.

        Args:
            sid_file: Parsed and loaded SID File with SID item assignment.
        """

        self.complete_model.schema_data.apply_sid_file(sid_file)
        self.complete_model.schema.apply_sid_file(sid_file)

        self.schema_data.copy_sids_from(self.complete_model.schema_data)
        self.schema.copy_sids_from(self.complete_model.schema, self.schema_data)

    def _build_complete_model(self, data_factory: yangson.schemadata.SchemaDataFactory, tree_factory: yangson.schemanode.SchemaTreeFactory):
        mods = []
        newest = {}
        for mod in self.schema_data.modules:
            # the revision-less modules has identifier ("name", "")
            known_rev = newest.get(mod[0])
            # unknown module yet
            if (known_rev is None or
                    # newer revision for this module
                    (known_rev and mod[1] != "" and
                    known_rev < mod[1])
                    # any revision is better than revisionless mod
                    or (not known_rev and mod[1] != "")):
                newest[mod[0]] = mod[1]

        def finish_module(obj, mods, schema_data, done, newest) -> None:
            yl_mod = copy.deepcopy(obj)
            yl_mod["conformance-type"] = "implement"

            mod_data = schema_data.modules[(yl_mod["name"], newest[yl_mod["name"]])]
            # Note that feature must be module toplevel statement only
            features = [stmt.argument for stmt in mod_data.statement.find_all("feature")]

            for submod_id in mod_data.submodules:
                submod_data = self.schema_data.modules[submod_id]
                features.extend([stmt.argument for stmt in submod_data.statement.find_all("feature")])

            yl_mod["feature"] = features
            done.add(yl_mod["name"])
            mods.append(yl_mod)

        done = set()
        for obj in self.yang_library["ietf-yang-library:modules-state"]["module"]:
            if (obj["conformance-type"] == "implement" or
                    (obj["conformance-type"] == "import" and obj["revision"] != "")):
                finish_module(obj, mods, self.schema_data, done, newest)

        for notdone in (name for name in newest.keys() if name not in done):
            for obj in self.yang_library["ietf-yang-library:modules-state"]["module"]:
                if obj["name"] == notdone:
                    finish_module(obj, mods, self.schema_data, done, newest)

        mod_path = self.schema_data.module_search_path
        yltext = json.dumps({"ietf-yang-library:modules-state": {"module-set-id": "0", "module": mods}})
        self.complete_model = yangson.datamodel.DataModel(yltext, mod_path,
                                                          data_factory=data_factory,
                                                          tree_factory=tree_factory)

    def ascii_tree(self, no_types: bool = False, val_count: bool = False, sid: bool = False, sid_price: bool = False) -> str:
        """Generate ASCII art representation of the schema tree.

        Args:
            no_types: Suppress output of data type info.
            val_count: Show accumulated validation counts.

        Returns:
            String with the ASCII tree.
        """
        return self.schema._ascii_tree("", no_types, val_count, sid=sid, sid_price=sid_price)

