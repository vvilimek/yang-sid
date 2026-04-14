import yangson.datamodel
import yangson.schemadata
import yangson.schemanode

from .schema import SchemaTreeFactory
from .schema_data import SchemaDataFactory

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
 

