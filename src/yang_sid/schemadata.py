# SPDX-FileCopyrightText: CZ.NIC z.s.p.o.
#
# SPDX-License-Identifier: LGPL-3.0-or-later

import yangson
import yangson.schemadata
import yangson.schemanode
import yangson.typealiases
from yangson.typealiases import QualName, ModuleId, YangIdentifier

from pathlib import Path
from collections.abc import Iterable, Mapping
from typing import ClassVar, Any, Union, Optional

from .sid_file import SidRepository, SidFile, SidFileLoader, ItemNamespace
from .schemanode import SchemaNode
from .types import SID

"""
Essential YANG schema structures and methods.

This module implements the following classes:

* ModuleData: Data related to a YANG module or submodule.
* ModuleDataFactory: Factory creating SID-aware module data.
* SchemaData: Repository of YANG schema structures and methods.
* SchemaDataFactory: Factory creating SID-aware schema data.
"""

class ModuleData(yangson.schemadata.ModuleData):
    """Data related to a YANG module or submodule. With SID support. """

    def __init__(self, main_module: yangson.typealiases.YangIdentifier, yang_id: yangson.typealiases.YangIdentifier) -> None:
        """Initialize the class instance."""

        super().__init__(main_module, yang_id)
        self.sid: Optional[SID] = None
        self.features_by_sid: dict[SID, YangIdentifier] = {}
        self.sid_features: dict[YangIdentifier, SID] = {}

class ModuleDataFactory:
    """Factory creating SID-aware module data."""

    def create_module_data(self, main_module: yangson.typealiases.YangIdentifier, yang_id: yangson.typealiases.YangIdentifier) -> yangson.schemadata.ModuleData:
        """Create module data with SID support.

        Args:
            main_module: YANG name of the enclosing module.
            yang_id: YANG name of the current module.

        Returns:
            Created module data.
        """
        return ModuleData(main_module, yang_id)

class SchemaData(yangson.schemadata.SchemaData):
    """Repository of YANG schema structures and utility methods.

    Args:
        yang_lib: Dictionary with YANG library data.
        mod_path: List of directories to search for YANG modules.
    """

    modules: Mapping[ModuleId, ModuleData]
    modules_by_name: Mapping[str, ModuleData]
    modules_by_ns: Mapping[str, ModuleData]

    module_data_factory: ClassVar[type] = ModuleDataFactory
    """Factory used for ModuleData initialization."""

    def __init__(self, yang_lib: dict[str, Any], mod_path: list[str]) -> None:
        """Initialize the schema structure with SID support."""

        super().__init__(yang_lib, mod_path)
        self.sid_path: tuple[str, ...] = tuple()
        """Search path for SID Files."""
        self.sid_repository = SidRepository()
        """Repository of all SID Files stored in the schema data."""
        self.modules_by_sid: dict[SID, ModuleData] = {}
        """Modules indexed by SID numbers."""
        self.identities_by_sid: dict[SID, QualName] = {}
        """Mapping from SID to associated identity."""
        self.sid_identities: dict[QualName, SID] = {}
        """Mapping from all implemented identities to their SIDs."""
        self.all_sids: dict[SID, Union[SchemaNode, QualName, str, ModuleData]] = {}
        """Library-global mapping of all known SIDs to related YANG item."""

    def set_sid_path(self, sid_path: Iterable[str]) -> None:
        """Set SID search path."""

        self.sid_path = tuple(sid_path)

    def find_sid_file(self, module: yangson.schemadata.ModuleData) -> Optional[Path]:
        """Search for SID Files containing assignment for given module.

        Args:
            module: SID File belonging to given module is searched.

        The search is done in all entiers of SID path.
        """

        return SidFileLoader.find_sid_file(module, self.sid_path)

    def load_sid_file(self, file: Path) -> SidFile:
        """Load SID File on given path."""

        return SidFileLoader.parse_sid_file(file)

    def validate_sids(self) -> None:
        """Validate that all SID assignment and other constraints are met."""

        raise NotImplementedError()

    def apply_sid_file(self, sid_file: SidFile) -> None:
        """Import SIDs from SID File to schema data attributes.

        SID Item assignment used are module SIDs, feature SIDs and identity SIDs."""

        for item in sid_file.item.values():
            match item.namespace:
                case ItemNamespace.MODULE:
                    # TODO submodule revision
                    rev = sid_file.revision if sid_file.revision else ""
                    mod_data = self.modules[(item.identifier, rev)]
                    mod_data.sid = item.sid
                    self.modules_by_sid[item.sid] = mod_data
                    self.all_sids[item.sid] = mod_data
                case ItemNamespace.IDENTITY:
                    qual_name = (item.identifier, sid_file.module)
                    self.identities_by_sid[item.sid] = qual_name
                    self.all_sids[item.sid] = qual_name
                    self.sid_identities[qual_name] = item.sid
                case ItemNamespace.FEATURE:
                    # TODO revision ""/None
                    rev = sid_file.revision if sid_file.revision else ""
                    mod_data = self.modules[(sid_file.module, rev)]
                    if mod_data.yang_id != mod_data.main_module:
                        mod_data = self.modules[mod_data.main_module]
                    if item.identifier not in mod_data.features:
                        continue

                    mod_data.features_by_sid[item.sid] = item.identifier
                    mod_data.sid_features[item.identifier] = item.sid

                    self.all_sids[item.sid] = item.identifier
                case _:
                    pass

class SchemaDataFactory:
    """Factory creating SID-aware schema data."""

    def create_schema_data(self, yang_lib: dict[str, Any], mod_path: list[str]) -> yangson.schemadata.SchemaData:
        """Create schema data with SID support from yang library with module search path.

        Args:
            yang_lib: From JSON parsed RFC 7895 YANG Library.
            mod_path: List of directories where modules are searched.

        Returns:
            Created schema data.
        """

        return SchemaData(yang_lib, mod_path)
