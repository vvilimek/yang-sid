# SPDX-FileCopyrightText: CZ.NIC z.s.p.o.
#
# SPDX-License-Identifier: LGPL-3.0-or-later

import yangson.schemanode
from yangson.statement import Statement
from yangson.schemadata import SchemaContext

from .types import SID

from typing import Optional

class SchemaMixin:
    def __init__(self) -> None:
        self.sid: Optional[SID] = None
        print("SchemaMixin __init__()")

class SchemaNode(SchemaMixin, yangson.schemanode.SchemaNode):
    def __init__(self) -> None:
        super().__init__()
        print("SchemaNode __init__()")

class InternalMixin(SchemaMixin):
    def __init__(self) -> None:
        super().__init__()
        self.children_by_sid: dict[SID, SchemaNode] = {}
        print("InternalMixin __init__()")

    def _anydata_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        self._handle_child(Anydata(), stmt, sctx)

    def _anyxml_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        self._handle_child(AnyxmlNode(), stmt, sctx)

    def _case_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        self._handle_child(CaseNode(), stmt, sctx)

    def _choice_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        self._handle_child(ChoiceNode(), stmt, sctx)

    def _container_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        self._handle_child(ContainerNode(), stmt, sctx)

    def _input_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        self._handle_child(InputNode(), stmt, sctx)

    def _leaf_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        self._handle_child(LeafNode(), stmt, sctx)

    def _leaf_list_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        self._handle_child(LeafListNode(), stmt, sctx)

    def _list_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        self._handle_child(ListNode(), stmt, sctx)

    def _notification_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        self._handle_child(NotificationNode(), stmt, sctx)

    def _output_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        self._handle_child(OutputNode(), stmt, sctx)

    def _rpc_action_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
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
        target = self.get_schema_descendant(
            sctx.schema_data.sni2route(stmt.argument, sctx))
        if target is None:      # silently ignore missing target
            return
        if isinstance(target._y_data_struct, yangson.schemanode.YangData):
            raise InvalidArgument("It is invalid to use 'augment' statement on ietf-restconf:yang-data.")
        if isinstance(target._y_data_struct, yangson.schemanode.Structure):
            raise InvalidArgument("It is invalid to use 'augment' statement on ietf-yang-structure-ext:structure.")
        if stmt.find1("when"):
            gr = GroupNode()
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
            sn = GroupNode()
            xpp = XPathParser(wst.argument, sctx)
            wex = xpp.parse()
            if not xpp.at_end():
                raise InvalidArgument(wst.argument)
            sn.when = wex
            self._add_child(sn)
        else:
            sn = self
        sn._handle_substatements(grp, gid)
        for augst in stmt.find_all("augment"):
            sn._augment_stmt(augst, sctx)
        for refst in stmt.find_all("refine"):
            sn._refine_stmt(refst, sctx)

class GroupMixin(InternalMixin):
    def __init__(self) -> None:
        super().__init__()
        print("GroupMixin __init__()")

    def _handle_child(self, node: yangson.schemanode.SchemaNode, stmt: Statement,
                      sctx: SchemaContext) -> None:
        if not isinstance(
                self.parent, yangson.schemanode.ChoiceNode) or isinstance(node, yangson.schemanode.CaseNode):
            super()._handle_child(node, stmt, sctx)
        else:
            cn = CaseNode()
            cn.name = stmt.argument
            cn.ns = sctx.default_ns
            self._add_child(cn)
            cn._handle_child(node, stmt, sctx)

class InternalNode(InternalMixin, yangson.schemanode.InternalNode):
    def __init__(self) -> None:
        super().__init__()
        print("InternalNode __init__()")

class GroupNode(GroupMixin, yangson.schemanode.GroupNode):
    def __init__(self) -> None:
        super().__init__()
        print("GroupNode __init__()")

class YangData(GroupMixin, yangson.schemanode.YangData):
    def __init__(self) -> None:
        super().__init__()
        print("YangData __init__()")

class SchemaTreeNode(GroupMixin, yangson.schemanode.SchemaTreeNode):
    def __init__(self, schemadata: Optional[yangson.schemadata.SchemaData] = None):
        super().__init__(schemadata)
        print("SchemaTreeNode __init__()")
        self.sid: Optional[SID] = None
        self.children_by_sid: dict[SID, "SchemaNode"] = {}

class DataNode(InternalMixin, yangson.schemanode.DataNode):
    def __init__(self) -> None:
        super().__init__()
        print("DataNode __init__()")

class TerminalNode(InternalMixin, yangson.schemanode.TerminalNode):
    def __init__(self) -> None:
        super().__init__()
        print("TerminalNode __init__()")

class ContainerNode(InternalMixin, yangson.schemanode.ContainerNode):
    def __init__(self) -> None:
        super().__init__()
        print("ContainerNode __init__()")

class Structure(InternalMixin, yangson.schemanode.Structure):
    def __init__(self) -> None:
        super().__init__()
        print("Structure __init__()")

class SequenceNode(InternalMixin, yangson.schemanode.SequenceNode):
    def __init__(self) -> None:
        super().__init__()
        print("SequenceNode __init__()")

class ListNode(InternalMixin, yangson.schemanode.ListNode):
    def __init__(self) -> None:
        super().__init__()
        print("ListNode __init__()")

class ChoiceNode(InternalMixin, yangson.schemanode.ChoiceNode):
    def __init__(self) -> None:
        super().__init__()
        print("ChoicoeNode __init__()")

class CaseNode(InternalMixin, yangson.schemanode.CaseNode):
    def __init__(self) -> None:
        super().__init__()
        print("CaseNode __init__()")

class LeafNode(SchemaMixin, yangson.schemanode.LeafNode):
    def __init__(self) -> None:
        super().__init__()
        print("LeafNode __init__()")

class LeafListNode(InternalMixin, yangson.schemanode.LeafListNode):
    def __init__(self) -> None:
        super().__init__()
        print("LeafListNode __init__()")

class AnyContentNode(InternalMixin, yangson.schemanode.AnyContentNode):
    def __init__(self) -> None:
        super().__init__()
        print("AnyContentNode __init__()")

class AnydataNode(InternalMixin, yangson.schemanode.AnydataNode):
    def __init__(self) -> None:
        super().__init__()
        print("AnydataNode __init__()")

class AnyxmlNode(InternalMixin, yangson.schemanode.AnyxmlNode):
    def __init__(self) -> None:
        super().__init__()
        print("AnyxmlNode __init__()")

class RpcActionNode(GroupMixin, yangson.schemanode.RpcActionNode):
    def __init__(self) -> None:
        super().__init__()
        print("RpcActionNode __init__()")

class InputNode(InternalMixin, yangson.schemanode.InputNode):
    def __init__(self) -> None:
        super().__init__()
        print("InputNode __init__()")

class OutputNode(InternalMixin, yangson.schemanode.OutputNode):
    def __init__(self) -> None:
        super().__init__()
        print("OutputNode __init__()")

class NotificationNode(GroupMixin, yangson.schemanode.NotificationNode):
    def __init__(self) -> None:
        super().__init__()
        print("NotificationNode __init__()")

class SchemaTreeFactory:
    def create_tree(self, schemadata: yangson.schemadata.SchemaData) -> SchemaTreeNode:
        return SchemaTreeNode(schemadata)



