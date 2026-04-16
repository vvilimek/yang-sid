import yangson.datamodel
import yangson.schemadata
import yangson.schemanode

from .schemanode import SchemaTreeFactory
from .schemadata import SchemaDataFactory, ModuleData
from .sid_file import SidFile

from pathlib import Path
from collections.abc import Iterable
from typing import Optional


class DataModel(yangson.datamodel.DataModel):
    """Basic user-level entry point to yang-sid library."""

    def __init__(self, yltxt: str, mod_path: tuple[str] = (".",),
                 description: Optional[str] = None,
                 data_factory = None, #: Optional[yangson.schemadata.SchemaDataFactory] = None,
                 tree_factory = None) -> None: #: Optional[yangson.schemanode.SchemaTreeFactory] = None) -> None:
        """Initialize the class instance.

        Args:
            yltxt: JSON text with YANG library data.
            mod_path: Tuple of directories where to look for YANG modules.
            description: Optional description of the data model.
            data_factory: Factory for getting SchemaData instance.
            tree_factory: Factory for getting SchemaTreeNode instance.

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

        return super().__init__(yltxt, mod_path, description, data_factory, tree_factory)

    def set_sid_path(self, sid_path: Iterable[str]) -> None:
        self.schema_data.set_sid_path(sid_path)

    def load_sid_file(self, file: str) -> SidFile:
        file = Path(file)
        parsed_file = self.schema_data.load_sid_file(file)
        self.schema_data.apply_sid_file(parsed_file)
        self.schema.apply_sid_file(parsed_file)
        return parsed_file

    def load_all_module_sids(self) -> None:
        for mod_id in self.schema_data.implement.items():
            mod = self.schema_data.modules[mod_id]
            self.load_module_sids(mod)

    def load_all_sid_files(self) -> None:
        self.load_all_module_sids()

    def load_module_sids(self, mod_data: ModuleData) -> bool:
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
        self.schema_data.apply_sid_file(sid_file)
        self.schema.apply_sid_file(sid_file)

