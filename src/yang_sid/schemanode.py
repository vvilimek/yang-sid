# SPDX-FileCopyrightText: CZ.NIC z.s.p.o.
#
# SPDX-License-Identifier: LGPL-3.0-or-later

import logging
import copy

import yangson.schemanode
import yangson.datatype
import yangson.xpathparser
import yangson.typealiases
import yangson.exceptions
from yangson.statement import Statement
from yangson.schemadata import SchemaContext

from .types import SID
from .schemadata import ModuleData, SchemaData
from .sid_file import SidFile, ItemNamespace

from typing import Optional, cast

dbg_logger = logging.getLogger("yang_sid.schema INIT")
dbg_logger.setLevel(logging.DEBUG)

logger = logging.getLogger(__name__)

class SchemaNode(yangson.schemanode.SchemaNode):
    """Abstract class with SID support for all SID-aware schema nodes."""

    parent: Optional["InternalNode"]

    def __init__(self) -> None:
        """Initialize the class instance."""

        super().__init__()
        self.sid: Optional[SID] = None
        dbg_logger.debug(f"SchemaNode __init__() {self.__class__.__name__}")

    # _follow_leafref  works without overriding, the YangData is derived from yangson.schemanode.YangData

class InternalNode(yangson.schemanode.InternalNode, SchemaNode):
    """Abstract class for SID-aware schema nodes that have children."""

    def __init__(self) -> None:
        """Initialize the class instance."""
        super().__init__()
        self.children_by_sid: dict[SID, SchemaNode] = {}
        dbg_logger.debug(f"InternalNode __init__() {self.__class__.__name__}")

    def _anydata_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        """Handle anydata statement."""
        self._handle_child(AnydataNode(), stmt, sctx)

    def _anyxml_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        """Handle anyxml statement."""
        self._handle_child(AnyxmlNode(), stmt, sctx)

    def _case_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        """Handle case statement."""
        self._handle_child(CaseNode(), stmt, sctx)

    def _choice_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        """Handle choice statement."""
        self._handle_child(ChoiceNode(), stmt, sctx)

    def _container_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        """Handle container statement."""
        self._handle_child(ContainerNode(), stmt, sctx)

    def _leaf_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        """Handle leaf statement."""
        node = LeafNode()
        node.type = yangson.datatype.DataType._resolve_type(
                cast(Statement, stmt.find1("type", required=True)), sctx)
        self._handle_child(node, stmt, sctx)

    def _leaf_list_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        """Handle leaf-list statement."""
        node = LeafListNode()
        node.type = yangson.datatype.DataType._resolve_type(
                cast(Statement, stmt.find1("type", required=True)), sctx)
        self._handle_child(node, stmt, sctx)

    def _list_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        """Handle list statement."""
        self._handle_child(ListNode(), stmt, sctx)

    def _notification_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        """Handle notification statement."""
        self._handle_child(NotificationNode(), stmt, sctx)

    def _rpc_action_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        """Handle rpc or action statement."""
        self._handle_child(RpcActionNode(), stmt, sctx)

    def _augment_stmt(self, stmt: Statement,
                      sctx: SchemaContext) -> None:
        """Handle **augment** statement."""
        # TODO augmenting YangData is forbidden
        if not sctx.schema_data.if_features(stmt, sctx.text_mid):
            # and \
            #not isinstance(self._y_data_struct, YangData):
            # ietf-restconf:yang-data ignores if-feature statements
            return
        assert stmt.argument is not None
        target = self.get_schema_descendant(
            sctx.schema_data.sni2route(stmt.argument, sctx))
        if target is None:      # silently ignore missing target
            return
        if isinstance(target._y_data_struct, yangson.schemanode.YangData):
            raise yangson.exceptions.InvalidArgument("It is invalid to use 'augment' statement on ietf-restconf:yang-data.")
        if isinstance(target._y_data_struct, yangson.schemanode.Structure):
            raise yangson.exceptions.InvalidArgument("It is invalid to use 'augment' statement on ietf-yang-structure-ext:structure.")
        if stmt.find1("when"):
            gr = GroupNode()
            assert isinstance(target, InternalNode)
            target._add_child(gr)
            target = gr
        target._handle_substatements(stmt, sctx)

    def _uses_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        """Handle uses statement."""
        # TODO is it possible to have if-feature here for YangData
        if not sctx.schema_data.if_features(stmt, sctx.text_mid) and \
                not isinstance(self._y_data_struct, yangson.schemanode.YangData):
            # ietf-restconf:yang-data ignores if-feature statements
            return
        grp, gid = sctx.schema_data.get_definition(stmt, sctx)
        wst = stmt.find1("when")
        if wst:
            sn: InternalNode = GroupNode()
            assert wst.argument is not None
            xpp = yangson.xpathparser.XPathParser(wst.argument, sctx)
            wex = xpp.parse()
            if not xpp.at_end():
                raise yangson.exceptions.InvalidArgument(wst.argument)
            sn.when = wex
            self._add_child(sn)
        else:
            sn = self
        sn._handle_substatements(grp, gid)
        for augst in stmt.find_all("augment"):
            sn._augment_stmt(augst, sctx)
        for refst in stmt.find_all("refine"):
            sn._refine_stmt(refst, sctx)


    # _schema_pattern works without overriding, the YangData is derived from yangson.schemanode.YangData
    # _handle_child works without overriding, the YangData is derived from yangson.schemanode.YangData
    # _augment_stmt works without overriding, both YangData and Structure are derived from yangson.schemanode.YangData, resp. yangson.schemanode.Structure
    # _ascii_tree works without overriding, both YangData and Structure are derived from yangson.schemanode.YangData, resp. yangson.schemanode.Structure
    # _refind_stmt works without overriding, the YangData is derived from yangson.schemanode.YangData
    # _uses_stmt works without overriding, the YangData is derived from yangson.schemanode.YangData
    # _identity_stmt works without overriding, the YangData is derived from yangson.schemanode.YangData
    # _ascii_tree works without overriding, both YangData and Structure are derived from yangson.schemanode.YangData, resp. yangson.schemanode.Structure


class GroupNode(yangson.schemanode.GroupNode, InternalNode):
    """Anonymous group of schema nodes with SID support."""

    def __init__(self) -> None:
        """Initialize the class instance."""
        super().__init__()
        dbg_logger.debug(f"GroupNode __init__() {self.__class__.__name__}")

    def _handle_child(self, node: yangson.schemanode.SchemaNode, stmt: Statement,
                      sctx: SchemaContext) -> None:
        """Add child node to the receiver and handle substatements."""
        if not isinstance(
                self.parent, yangson.schemanode.ChoiceNode) or isinstance(node, yangson.schemanode.CaseNode):
            super()._handle_child(node, stmt, sctx)
        else:
            cn = CaseNode()
            cn.name = stmt.argument
            cn.ns = sctx.default_ns
            self._add_child(cn)
            cn._handle_child(node, stmt, sctx)

class YangData(yangson.schemanode.YangData, GroupNode):
    """Standard ietf-restconf:yang-data node."""

    def __init__(self) -> None:
        """Initialize the class instance."""
        super().__init__()
        dbg_logger.debug(f"YangData __init__() {self.__class__.__name__}")

class SchemaTreeNode(yangson.schemanode.SchemaTreeNode, GroupNode):
    """Root node of a schema tree with SIDs."""

    schema_data: Optional[SchemaData]

    def __init__(self, schemadata: Optional[yangson.schemadata.SchemaData] = None):
        """Initialize the class instance."""
        if schemadata and not isinstance(schemadata, SchemaData):
            raise TypeError("yang_sid.SchemaTreeNode requires schema data with SID support.")
        super().__init__(schemadata)
        dbg_logger.debug(f"SchemaTreeNode __init__() {self.__class__.__name__}")

    def apply_sid_file(self, sid_file: SidFile) -> None:
        """Assign SIDs from SID File descendant schema nodes."""
        for item in sid_file.item.values():
            if item.namespace != ItemNamespace.DATA:
                continue

            # TODO: Test RPC, ACTION, NOTIFICATION, YANG_DATA, SX_STRUCTURE
            if not self.schema_data:
                raise ValueError("Schema tree must have access to schema data to set SID numbers.")
            route = self.schema_data.path2route(item.identifier)
            node = self.get_schema_descendant(route)
            if not self.schema_data:
                raise ValueError("Schema tree node must have access to schema data to add SID numbers.")
            if node:
                assert isinstance(node, SchemaNode), "Code invariant broken, expected schema node with SID"
                node.sid = item.sid
                self.schema_data.all_sids[item.sid] = node
                if node.parent:
                    node.parent.children_by_sid[item.sid] = node
            else:
                logger.warning(f"Unsupported node identified by {item.identifier}")

    def _sx_structure_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        """Handle ietf-yang-structure-ext:structure statement."""
        struct = Structure()
        self._handle_child(struct, stmt, sctx)

    def _rc_yang_data_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        """Handle the ietf-restconf:yang-data statement."""
        # TODO: XXX: Fix possibly missing SIDs of modules, features, identities, ...
        yd_sch_data = cast(SchemaData, copy.copy(sctx.schema_data))
        # We cannot afford to use SchemaData constructor as it requires YANG Library as dict
        sd = sctx.schema_data
        if not isinstance(sd, SchemaData):
            raise TypeError("yang_sid.SchemaTreeNode requires schema data with SIDs.")
        main_mod: ModuleData = sd.modules[sctx.text_mid]
        accessible_mods: list[yangson.typealiases.ModuleId] = []
        mod_stack: list[ModuleData] = []
        mod_stack.append(main_mod)
        while len(mod_stack) > 0:
            mod = mod_stack.pop()
            accessible_mods.append(mod.main_module)
            accessible_mods.extend(mod.submodules)
            for imported_mod in mod.prefix_map.values():
                if imported_mod in accessible_mods:
                    continue
                mod_stack.append(sd.modules[imported_mod])

        yd_sch_data.modules = {mid: mod_data for (mid, mod_data) in sd.modules.items() if mid in accessible_mods}

        accessible_names = list(map(lambda mid: mid[0], accessible_mods))
        yd_sch_data.identity_adjs = sd.identity_adjs
        #yd_sch_data.identity_adjs = {qn: ident for (qn, ident) in sd.identity_adjs if qn[1] in accessible_names}
        yd_sch_data.modules_by_name = {name: mod_data for (name, mod_data) in sd.modules_by_name.items()
                                       if name in accessible_names}
        namespaces = [mod_data.xml_namespace for mod_data in yd_sch_data.modules.values()]
        yd_sch_data.modules_by_ns = {ns: mod_data for (ns, mod_data) in sd.modules_by_ns.items() if ns in namespaces}
        #  TODO the _module_sequence is built in online fashion meaning it most likely contain only prefix of final schema_data._module_sequence
        yd_sch_data._module_sequence = [mod for mod in yd_sch_data._module_sequence if mod in accessible_mods]

        # The if-feature statement are to be ignored, we simply enable all possible feature
        yd_sctx = SchemaContext(yd_sch_data, sctx.default_ns, sctx.text_mid)
        yang_data = YangData()
        self._handle_child(yang_data, stmt, yd_sctx)

    # _augment_stmt works without overriding, the Structure is derived from yangson.schemanode.Structure

class DataNode(yangson.schemanode.DataNode, SchemaNode):
    """Abstract superclass for all data nodes with SIDs."""
    def __init__(self) -> None:
        """Initialize the class instance."""
        super().__init__()
        dbg_logger.debug(f"DataNode __init__() {self.__class__.__name__}")

class TerminalNode(yangson.schemanode.TerminalNode, SchemaNode):
    """Abstract superclass for terminal nodes with SIDs in the schema tree."""

    def __init__(self) -> None:
        """Initialize the class instance."""
        super().__init__()
        dbg_logger.debug(f"TerminalNode __init__() {self.__class__.__name__}")

class ContainerNode(yangson.schemanode.ContainerNode, InternalNode):
    """Container node with SIDs."""

    def __init__(self) -> None:
        """Initialize the class instance."""
        super().__init__()
        dbg_logger.debug(f"ContainerNode __init__() {self.__class__.__name__}")

class Structure(yangson.schemanode.Structure, InternalNode):
    """ietf-yang-structure-ext:structure node with SIDs."""

    def __init__(self) -> None:
        """Initialize the class instance."""
        super().__init__()
        dbg_logger.debug(f"Structure __init__() {self.__class__.__name__}")


class SequenceNode(yangson.schemanode.SequenceNode, SchemaNode):
    """Abstract class for data nodes with SIDs that represent a sequence."""

    def __init__(self) -> None:
        """Initialize the class instance."""
        super().__init__()
        dbg_logger.debug(f"SequenceNode __init__() {self.__class__.__name__}")

class ListNode(yangson.schemanode.ListNode, InternalNode):
    """List node with SIDs."""

    def __init__(self) -> None:
        """Initialize the class instance."""
        super().__init__()
        dbg_logger.debug(f"ListNode __init__() {self.__class__.__name__}")

class ChoiceNode(yangson.schemanode.ChoiceNode, InternalNode):
    """Choice node with SIDs."""

    def __init__(self) -> None:
        """Initialize the class instance."""
        super().__init__()
        dbg_logger.debug(f"ChoicoeNode __init__() {self.__class__.__name__}")

class CaseNode(yangson.schemanode.CaseNode, InternalNode):
    """Case node with SIDs."""

    def __init__(self) -> None:
        super().__init__()
        dbg_logger.debug(f"CaseNode __init__() {self.__class__.__name__}")

class LeafNode(yangson.schemanode.LeafNode, SchemaNode):
    """Leaf node with SIDs."""

    def __init__(self) -> None:
        super().__init__()
        dbg_logger.debug(f"LeafNode __init__() {self.__class__.__name__}")

class LeafListNode(yangson.schemanode.LeafListNode, SchemaNode):
    """Leaf-list node with SIDs."""
    def __init__(self) -> None:
        super().__init__()
        dbg_logger.debug(f"LeafListNode __init__() {self.__class__.__name__}")

class AnyContentNode(yangson.schemanode.AnyContentNode, SchemaNode):
    """Abstract class for anydata or anyxml nodes with SIDs."""

    def __init__(self) -> None:
        super().__init__()
        dbg_logger.debug(f"AnyContentNode __init__() {self.__class__.__name__}")

class AnydataNode(yangson.schemanode.AnydataNode, SchemaNode):
    """Anydata node with SIDs."""

    def __init__(self) -> None:
        super().__init__()
        dbg_logger.debug(f"AnydataNode __init__() {self.__class__.__name__}")

class AnyxmlNode(yangson.schemanode.AnyxmlNode, SchemaNode):
    """Anyxml node with SIDs."""

    def __init__(self) -> None:
        super().__init__()
        dbg_logger.debug(f"AnyxmlNode __init__() {self.__class__.__name__}")

class RpcActionNode(yangson.schemanode.RpcActionNode, GroupNode):
    """RPC or action node with SIDs."""

    def __init__(self) -> None:
        super().__init__()
        dbg_logger.debug(f"RpcActionNode __init__() {self.__class__.__name__}")

    def _input_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        """Handle RPC or action input statement."""
        cast(SchemaNode, self.get_child("input"))._handle_substatements(stmt, sctx)

    def _output_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        """Handle RPC or action output statement."""
        cast(SchemaNode, self.get_child("output"))._handle_substatements(stmt, sctx)

    def _handle_substatements(self, stmt: Statement, sctx: SchemaContext) -> None:
        """Dispatch actions for substatements of `stmt`."""
        self._add_child(InputNode(sctx.default_ns))
        self._add_child(OutputNode(sctx.default_ns))
        super()._handle_substatements(stmt, sctx)

class InputNode(yangson.schemanode.InputNode, InternalNode):
    """RPC or action input node with SIDs."""
    def __init__(self, ns) -> None:
        super().__init__(ns)
        dbg_logger.debug(f"InputNode __init__() {self.__class__.__name__}")

class OutputNode(yangson.schemanode.OutputNode, InternalNode):
    """RPC or action output node with SIDs."""

    def __init__(self, ns) -> None:
        super().__init__(ns)
        dbg_logger.debug(f"OutputNode __init__() {self.__class__.__name__}")

class NotificationNode(yangson.schemanode.NotificationNode, GroupNode):
    """Notification node with SIDs."""

    def __init__(self) -> None:
        super().__init__()
        dbg_logger.debug(f"NotificationNode __init__() {self.__class__.__name__}")

class SchemaTreeFactory:
    """Factory creating SID-aware schema tree."""

    def create_tree(self, schemadata: yangson.schemadata.SchemaData) -> yangson.schemanode.SchemaTreeNode:
        """Create schema tree from schema data.

        Args:
            schemadata: Holds repository of YANG modules for which the data model schema tree should be built.

        Returns:
            Created schema tree node with SID support.
        """
        return SchemaTreeNode(schemadata)

