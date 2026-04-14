# SPDX-FileCopyrightText: CZ.NIC z.s.p.o.
#
# SPDX-License-Identifier: LGPL-3.0-or-later

import yangson.schemanode
from yangson.statement import Statement
from yangson.schemadata import SchemaContext

from .types import SID

from typing import Optional

class SchemaNode(yangson.schemanode.SchemaNode):
    def __init__(self) -> None:
        super().__init__()
        self.sid = Optional[SID] = None

class InternalNode(SchemaNode, yangson.schemanode.InternalNode):
    def __init__(self) -> None:
        super().__init__()
        self.children_by_sid: dict[SID, SchemaNode] = {}

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

class GroupNode(InternalNode, yangson.schemanode.GroupNode):
    pass

class YangData(GroupNode, yangson.schemanode.YangData):
    def __init__(self) -> None:

        super().__init__()

class SchemaTreeNode(GroupNode, yangson.schemanode.SchemaTreeNode):
    def __init__(self, schemadata: Optional[yangson.schemadata.SchemaData] = None):
        super(yangson.schemanode.SchemaTreeNode, self).__init__(schemadata)
        self.sid: Optional[SID] = None
        self.children_by_sid: dict[SID, "SchemaNode"] = {}

class DataNode(SchemaNode, yangson.schemanode.DataNode):
    pass

class TerminalNode(SchemaNode, yangson.schemanode.TerminalNode):
    pass

class ContainerNode(DataNode, InternalNode, yangson.schemanode.ContainerNode):
    pass

class Structure(InternalNode, yangson.schemanode.Structure):
    pass

class SequenceNode(DataNode, yangson.schemanode.SequenceNode):
    pass

class ListNode(SequenceNode, InternalNode, yangson.schemanode.ListNode):
    pass

class ChoiceNode(InternalNode, yangson.schemanode.ChoiceNode):
    pass

class CaseNode(InternalNode, yangson.schemanode.CaseNode):
    pass

class LeafNode(DataNode, TerminalNode, yangson.schemanode.LeafNode):
    pass

class LeafListNode(SequenceNode, TerminalNode, yangson.schemanode.LeafListNode):
    pass

class AnyContentNode(DataNode, yangson.schemanode.AnyContentNode):
    pass

class AnydataNode(AnyContentNode, yangson.schemanode.AnydataNode):
    pass

class AnyxmlNode(AnyContentNode, yangson.schemanode.AnyxmlNode):
    pass

class RpcActionNode(SchemaTreeNode, yangson.schemanode.RpcActionNode):
    pass

class InputNode(InternalNode, DataNode, yangson.schemanode.InputNode):
    pass

class OutputNode(InternalNode, DataNode, yangson.schemanode.OutputNode):
    pass

class NotificationNode(SchemaTreeNode, yangson.schemanode.NotificationNode):
    pass

class SchemaTreeFactory:
    def create_tree(self, schemadata: yangson.schemadata.SchemaData) -> SchemaTreeNode:
        return SchemaTreeNode(schemadata)



