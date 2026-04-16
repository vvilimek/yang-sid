# SPDX-FileCopyrightText: CZ.NIC z.s.p.o.
#
# SPDX-License-Identifier: LGPL-3.0-or-later

import yangson
import yangson.schemadata
import yangson.schemanode
import yangson.typealiases
from yangson.typealiases import QualName

from pathlib import Path
from collections.abc import Iterable
from typing import ClassVar, Any, Union, Optional

from .sid_file import SidRepository, SidFile, SidFileLoader, ItemNamespace


class ModuleData(yangson.schemadata.ModuleData):
    def __init__(self, main_module: yangson.typealiases.YangIdentifier, yang_id: yangson.typealiases.YangIdentifier) -> None:
        super().__init__(main_module, yang_id)
        self.sid: Optional[SID] = None
        self.features_by_sid: dict[YangIdentifier, SID] = {}
        self.sid_features: dict[SID, YangIdentifier] = {}

class ModuleDataFactory:
    def create_module_data(self, main_module: yangson.typealiases.YangIdentifier, yang_id: yangson.typealiases.YangIdentifier) -> yangson.schemadata.ModuleData:
        return ModuleData(main_module, yang_id)

class SchemaData(yangson.schemadata.SchemaData):
    module_data_factory: ClassVar[type] = ModuleDataFactory

    def __init__(self, yang_lib: dict[str, Any], mod_path: list[str]) -> None:
        super().__init__(yang_lib, mod_path)
        self.sid_path: tuple[str, ...] = tuple()
        self.sid_repository = SidRepository()
        self.modules_by_sid: dict[SID, ModuleData] = {}
        self.identities_by_sid: dict[SID, QualName] = {}
        self.sid_identities: dict[QualName, SID] = {}
        self.all_sids: dict[SID, Union[SchemaNode, QualName, str, ModuleData]] = {}

    def set_sid_path(self, sid_path: Iterable[str]) -> None:
        self.sid_path = tuple(sid_path)

    def find_sid_file(self, module: yangson.schemadata.ModuleData) -> Optional[Path]:
        return SidFileLoader.find_sid_file(module, self.sid_path)

    def load_sid_file(self, file: Path) -> SidFile:
        return SidFileLoader.parse_sid_file(file)

    def validate_sids(self) -> None:
        raise NotImplementedException()

    def apply_sid_file(self, sid_file: SidFile) -> None:
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
                    mod_data = self.modules[(sid_file.module, sid_file.revision)]
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
    def create_schema_data(self, yang_lib: dict[str, Any], mod_path: list[str]) -> yangson.schemadata.SchemaData:
        return SchemaData(yang_lib, mod_path)
