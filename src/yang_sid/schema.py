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
        self.sid = Optional[SID] = None
        print("SchemaMixin __init__()")

class SchemaNode(SchemaMixin, yangson.schemanode.SchemaNode):
    def __init__(self) -> None:
        super().__init__()
        print("SchemaNode __init__()")

class InternalMixin(SchemaMixin):
    def __init__(self) -> None:
        super().__init__()
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


class InternalNode(InternalMixin, yangson.schemanode.InternalNode):
    def __init__(self) -> None:
        super().__init__()
        print("InternalNode __init__()")

class GroupNode(InternalMixin, yangson.schemanode.GroupNode):
    def __init__(self) -> None:
        super().__init__()
        print("GroupNode __init__()")

class YangData(InternalMixin, yangson.schemanode.YangData):
    def __init__(self) -> None:
        super().__init__()
        print("YangData __init__()")

class SchemaTreeNode(InternalMixin, yangson.schemanode.SchemaTreeNode):
    def __init__(self, schemadata: Optional[yangson.schemadata.SchemaData] = None):
        super(yangson.schemanode.SchemaTreeNode, self).__init__(schemadata)
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
    def __init__(self) -> None;
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

class ListNode(SequenceNode, InternalNode, yangson.schemanode.ListNode):
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

class LeafNode(DataNode, TerminalNode, yangson.schemanode.LeafNode):
    def __init__(self) -> None:
        super().__init__()
        print("LeafNode __init__()")

class LeafListNode(SequenceNode, TerminalNode, yangson.schemanode.LeafListNode):
    def __init__(self) -> None:
        super().__init__()
        print("LeafListNode __init__()")

class AnyContentNode(DataNode, yangson.schemanode.AnyContentNode):
    def __init__(self) -> None:
        super().__init__()
        print("AnyContentNode __init__()")

class AnydataNode(AnyContentNode, yangson.schemanode.AnydataNode):
    def __init__(self) -> None:
        super().__init__()
        print("AnydataNode __init__()")

class AnyxmlNode(AnyContentNode, yangson.schemanode.AnyxmlNode):
    def __init__(self) -> None:
        super().__init__()
        print("AnyxmlNode __init__()")

class RpcActionNode(SchemaTreeNode, yangson.schemanode.RpcActionNode):
    def __init__(self) -> None:
        super().__init__()
        print("RpcActionNode __init__()")

class InputNode(InternalNode, DataNode, yangson.schemanode.InputNode):
    def __init__(self) -> None:
        super().__init__()
        print("InputNode __init__()")

class OutputNode(InternalNode, DataNode, yangson.schemanode.OutputNode):
    def __init__(self) -> None:
        super().__init__()
        print("OutputNode __init__()")

class NotificationNode(SchemaTreeNode, yangson.schemanode.NotificationNode):
    def __init__(self) -> None:
        super().__init__()
        print("NotificationNode __init__()")

class SchemaTreeFactory:
    def create_tree(self, schemadata: yangson.schemadata.SchemaData) -> SchemaTreeNode:
        return SchemaTreeNode(schemadata)



