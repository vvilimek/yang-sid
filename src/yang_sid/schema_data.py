# SPDX-FileCopyrightText: CZ.NIC z.s.p.o.
#
# SPDX-License-Identifier: LGPL-3.0-or-later

import yangson
import yangson.schemadata
import yangson.schemanode
import yangson.typealiases

from .sid_file import SidRepository

from typing import ClassVar, Any

class ModuleData(yangson.schemadata.ModuleData):
    def __init__(self, main_module: yangson.typealiases.YangIdentifier, yang_id: yangson.typealiases.YangIdentifier) -> None:
        super().__init__(main_module, yang_id)
        self.sid: Optional[SID] = None
        self.sid_feature: dict[SID, YangIdentifier] = {}

class ModuleDataFactory:
    def create_module_data(self, main_module: yangson.typealiases.YangIdentifier, yang_id: yangson.typealiases.YangIdentifier) -> yangson.schemadata.ModuleData:
        return ModuleData(main_module, yang_id)

class SchemaData(yangson.schemadata.SchemaData):
    module_data_factory: ClassVar[type] = ModuleDataFactory

    def __init__(self, yang_lib: dict[str, Any], mod_path: list[str]) -> None:
        super().__init__(yang_lib, mod_path)
        self.sid_repository = SidRepository()

    def load_all_sid_files(self, schema: yangson.schemanode.SchemaTreeNode, non_std_filename: bool = False) -> None:
        for mod in self.modules_by_name.values():
            self.sid_repository.load_sid_file(module, non_std_filename)

    def load_sid_file(self, module: ModuleData, non_std_filename: bool = False) -> None:
        self.sid_repository.load_sid_file(module, non_std_filename)

class SchemaDataFactory:
    def create_schema_data(self, yang_lib: dict[str, Any], mod_path: list[str]) -> yangson.schemadata.SchemaData:
        return SchemaData(yang_lib, mod_path)
