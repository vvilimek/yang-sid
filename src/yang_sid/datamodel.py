# SPDX-FileCopyrightText: CZ.NIC z.s.p.o.
#
# SPDX-License-Identifier: LGPL-3.0-or-later

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
                 data_factory = None, #: Optional[yangson.schemadata.SchemaDataFactory] = None,
                 tree_factory = None) -> None: #: Optional[yangson.schemanode.SchemaTreeFactory] = None) -> None:
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

    def set_sid_path(self, sid_path: Iterable[str]) -> None:
        """Set search path for SID Files."""

        self.schema_data.set_sid_path(sid_path)

    def load_sid_file(self, file: Union[str, Path]) -> SidFile:
        """Load a SID File from given path.

        Args:
            file: Path to file to be loaded.
        """

        file = Path(file)
        parsed_file = self.schema_data.load_sid_file(file)
        self.schema_data.apply_sid_file(parsed_file)
        self.schema.apply_sid_file(parsed_file)
        return parsed_file

    def load_all_module_sids(self) -> None:
        """Search and load all SID Files on the SID path for YANG modules from loaded library."""

        for mod_id in self.schema_data.implement.items():
            mod = self.schema_data.modules[mod_id]
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
        for dep_rev in parsed.dependency_revision.values():
            dep_mod_data = self.schema_data.modules[(dep_rev.name, dep_rev.revision)]
            # There must not be cycles in the module imports
            if not self.load_module_sids(dep_mod_data):
                return False
        return True

    def apply_sid_file(self, sid_file: SidFile) -> None:
        """Use SID item assignments from loaded and parsed SID File on the schema tree as well as the schema data.

        Args:
            sid_file: Parsed and loaded SID File with SID item assignment.
        """

        self.schema_data.apply_sid_file(sid_file)
        self.schema.apply_sid_file(sid_file)

