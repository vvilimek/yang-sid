# SPDX-FileCopyrightText: CZ.NIC z.s.p.o.
#
# SPDX-License-Identifier: LGPL-3.0-or-later

import logging
import copy
from collections.abc import Iterator

import yangson.schemanode
import yangson.datatype
import yangson.xpathparser
import yangson.typealiases
import yangson.exceptions
from yangson.statement import Statement
from yangson.schemadata import SchemaContext
from yang_sid_base import SID, RelativeSID

from .schemadata import ModuleData, SchemaData
from .sid_file import SidFile, ItemNamespace

from typing import Optional, Union, cast

dbg_logger = logging.getLogger("yang_sid.schema INIT")
dbg_logger.setLevel(logging.CRITICAL)

logger = logging.getLogger(__name__)

class SchemaNode(yangson.schemanode.SchemaNode):
    """Abstract class with SID support for all SID-aware schema nodes."""

    parent: Optional["InternalNode"]
    sid_prices: tuple[tuple[int, int]] = (
            (23, 1), # 23, len(cbor2.dumps(23))
            (255, 2), # 2**8 - 1, len(cbor2.dumps(255))
            (65535, 3), # 2**16 - 1, len(cbor2.dumps(65535))
            (4294967295, 5), # 2**32 - 1, len(cbor2.dumps(4294967295))
            (18446744073709551615, 9), # 2**64-1, len(cbor2.dumps(18446744073709551615))
            )

    def __init__(self) -> None:
        """Initialize the class instance."""

        super().__init__()
        self.sid: Optional[SID] = None
        dbg_logger.debug(f"SchemaNode __init__() {self.__class__.__name__}")

    def has_complete_sid_map(self) -> bool:
        return False

    def get_price(self) -> Optional[int]:
        parent = self.parent
        assert parent is not None

        if self.sid is None:
            return None

        try:
            # Note that for SchemaTreeNode (toplevel pseudo-node)
            # the algorithm works as if it was relative.
            # This node has SID(0) so everything works as expected
            if isinstance(parent, ChoiceNode):
                assert parent.parent is not None
                if parent.parent.sid is None:
                    return None
                delta = self.sid - parent.parent.sid
            elif isinstance(parent, CaseNode):
                choice = parent.parent
                assert choice is not None
                parent = choice.parent
                assert parent is not None
                if parent.sid is None:
                    return None
                delta = self.sid - parent.sid
            elif isinstance(parent, YangData):
                assert parent.parent is not None
                if parent.parent.sid is None:
                    return None
                delta = self.sid - parent.parent.sid
            else:
                if parent.sid is None:
                    return None
                delta = self.sid - parent.sid
        except Exception as e:
            # TODO the price of the string should be considered
            raise ValueError(f"Missing SID for price calculation {self.as_schema_route()}") from e

        return self._absolute_price(delta)        

    @classmethod
    def _absolute_price(cls, sid: Union[SID, RelativeSID, None]) -> int:
        for (limit, price) in cls.sid_prices:
            if int(sid) <= limit:
                return price

        raise ValueError("SID number MUST be 63-bit number, " +
                         "the larget limit is 64-bit but the SID number is even larger.")

    def _tree_line(self, no_type: bool = False, ctype: bool = True, sid: bool = False, sid_price: bool = False) -> str:
        """Return the receiver's contribution to tree diagram."""
        line = super()._tree_line(no_type, ctype)
        if sid and self.sid:
            line = line + f" {self.sid}"
        elif sid and not isinstance(self, (ChoiceNode, CaseNode, YangData)):
            line = line + " unknown sid"
        price = self.get_price()
        if sid_price and price is not None:
            line = line + f" price {price}"
        return line

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

    def has_complete_sid_map(self) -> bool:
        if self.sid is None:
            return False

        for child in self.children:
            if not child.has_complete_sid_map():
                return False

    def _ascii_tree(self, indent: str, no_types: bool, val_count: bool, ctype: bool = True, sid: bool = False, sid_price: bool = False) -> str:
        """Return the receiver's subtree as ASCII art."""
        def suffix(sn):
            return f" {{{sn.val_count}}}\n" if val_count and isinstance(
                sn, (SchemaTreeNode, DataNode)) else "\n"
        if not self.children:
            return ""
        cs = []
        for c in filter(lambda c: not isinstance(c, (YangData, Structure)), self.children):
            cs.extend(c._flatten())
        cs.sort(key=lambda x: x.qual_name)
        # yang-data children
        ydcs = []
        for ydc in filter(lambda c: isinstance(c, YangData), self.children):
            ydcs.append(ydc)
        # structure children
        scs = []
        for sc in filter(lambda c: isinstance(c, Structure), self.children):
            scs.append(sc)
        res = ""
        for c in cs[:-1]:
            import inspect
            if 'sid' not in inspect.signature(c._tree_line)._parameters:
                breakpoint()
            res += (indent + c._tree_line(no_types, ctype, sid=sid, sid_price=sid_price) + suffix(c) +
                    c._ascii_tree(indent + "|  ", no_types, val_count, ctype, sid=sid, sid_price=sid_price))
        if len(cs) > 0:
            res += (indent + cs[-1]._tree_line(no_types, ctype, sid=sid, sid_price=sid_price) + suffix(cs[-1]) +
                cs[-1]._ascii_tree(indent + "   ", no_types, val_count, ctype, sid=sid, sid_price=sid_price))
        for ydc in ydcs:
            res += (ydc._tree_line(no_types, False, sid=sid, sid_price=sid_price) + suffix(ydc) +
                    ydc._ascii_tree(indent + "   ", no_types, val_count, False, sid=sid, sid_price=sid_price))
        for sc in scs:
            res += (sc._tree_line(no_types, False, sid=sid, sid_price=sid_price) + suffix(sc) +
                sc._ascii_tree(indent + "   ", no_types, val_count, False, sid=sid, sid_price=sid_price))
        return res

    def _tree_line(self, no_type: bool = False, ctype: bool = True, sid: bool = False, sid_price: bool = False) -> str:
        """Return the receiver's contribution to tree diagram."""
        return SchemaNode._tree_line(self, no_type, ctype, sid=sid, sid_price=sid_price)

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

    def _ascii_tree(self, indent: str, no_types: bool, val_count: bool, ctype: bool = True, sid: bool = False, sid_price: bool = False) -> str:
        """Return the receiver's subtree as ASCII art."""
        return InternalNode._ascii_tree(self, indent, no_types, val_count, ctype, sid=sid, sid_price=sid_price)

    def _tree_line(self, no_type: bool = False, ctype: bool = True, sid: bool = False, sid_price: bool = False) -> str:
        """Return the receiver's contribution to tree diagram."""
        return SchemaNode._tree_line(self, no_type, ctype, sid=sid, sid_price=sid_price)

class YangData(yangson.schemanode.YangData, GroupNode):
    """Standard ietf-restconf:yang-data node."""

    def __init__(self, sctx: Optional[SchemaContext] = None) -> None:
        """Initialize the class instance."""
        super().__init__(sctx)
        dbg_logger.debug(f"YangData __init__() {self.__class__.__name__}")

    def get_price(self) -> Optional[int]:
        return None

    def _ascii_tree(self, indent: str, no_types: bool, val_count: bool, ctype: bool = True, sid: bool = False, sid_price: bool = False) -> str:
        """Return the receiver's subtree as ASCII art."""
        def suffix(sn):
            return f" {{{sn.val_count}}}\n" if val_count else "\n"
        if not self.children:
            return ""

        c = self.children[0]
        return (indent + c._tree_line(no_types, False, sid=sid, sid_price=sid_price) + suffix(c) +
                c._ascii_tree(indent + "   ", no_types, val_count, False, sid=sid, sid_price=sid_price))

    def _tree_line(self, no_type: bool = False, ctype: bool = True, sid: bool = False, sid_price: bool = False) -> str:
        """Return the receiver's contribution to tree diagram."""
        return SchemaNode._tree_line(self, no_type, ctype, sid=sid, sid_price=sid_price)

class SchemaTreeNode(yangson.schemanode.SchemaTreeNode, GroupNode):
    """Root node of a schema tree with SIDs."""

    schema_data: Optional[SchemaData]

    def __init__(self, schemadata: Optional[yangson.schemadata.SchemaData] = None):
        """Initialize the class instance."""
        if schemadata and not isinstance(schemadata, SchemaData):
            raise TypeError("yang_sid.SchemaTreeNode requires schema data with SID support.")
        super().__init__(schemadata)
        dbg_logger.debug(f"SchemaTreeNode __init__() {self.__class__.__name__}")
        self.sid = SID(0)

    def apply_sid_file(self, sid_file: SidFile) -> None:
        """Assign SIDs from SID File descendant schema nodes."""
        for item in sid_file.item.values():
            if item.namespace != ItemNamespace.DATA:
                continue

            # TODO: Test RPC, ACTION, NOTIFICATION, YANG_DATA, SX_STRUCTURE
            if not self.schema_data:
                raise ValueError("Schema tree node must have access to schema data to set SID numbers.")
            route = self.schema_data.nid2route(item.identifier, self)
            if not route:
                raise ValueError(item.identifier)
            node = self.get_schema_descendant(route)
            if node:
                assert isinstance(node, SchemaNode), "Code invariant broken, expected schema node with SID"
                node.sid = item.sid
                self.schema_data.all_sids[item.sid] = node
                if node.parent:
                    if isinstance(node.parent, CaseNode):
                        case = node.parent
                        choice = node.parent.parent
                        choice_parent = node.parent.parent.parent

                        case.children_by_sid[item.sid] = node
                        choice.children_by_sid[item.sid] = node
                        if choice_parent:
                            choice_parent.children_by_sid[item.sid] = node
                    else:
                        node.parent.children_by_sid[item.sid] = node
            else:
                logger.warning(f"Unsupported node identified by {item.identifier}")

    def copy_sids_from(self, source: "SchemaTreeNode", schema_data: SchemaData) -> None:
        node = self
        foreign = source

        while node is not None:
            node.sid = foreign.sid
            schema_data.all_sids[node.sid] = node

            if isinstance(node, InternalNode) and len(node.children) > 0:
                node.children_by_sid = {sid: node.get_child(*child.qual_name) for (sid, child) in foreign.children_by_sid.items()
                                        if child.qual_name in map(lambda n: n.qual_name, node.children)}
                for choice in foreign.children:
                    if not isinstance(choice, ChoiceNode):
                        continue
                    for sid, foreign_child in choice.children_by_sid.items():
                        choice = foreign_child.parent.parent
                        case = foreign_child.parent
                        route = [choice.qual_name, case.qual_name, foreign_child.qual_name]
                        local_child = node.get_schema_descendant(route)
                        node.children_by_sid[sid] = local_child

                node = node.children[0]
                foreign = foreign.get_child(*node.qual_name)
                assert foreign is not None
            else:
                last = node
                node = node.parent
                foreign = foreign.parent
                while node and node.children.index(last) + 1 == len(node.children):
                    last = node
                    node = node.parent
                    foreign = foreign.parent

                if node:
                    node = node.children[node.children.index(last) + 1]
                    foreign = foreign.get_child(*node.qual_name)
                    assert foreign is not None

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
        yang_data = YangData(yd_sctx)
        self._handle_child(yang_data, stmt, yd_sctx)

    def get_price(self) -> Optional[int]:
        return None

    def _tree_line(self, no_type: bool = False, ctype: bool = True, sid: bool = False, sid_price: bool = False) -> str:
        """Return the receiver's contribution to tree diagram."""
        return SchemaNode._tree_line(self, no_type, ctype, sid=sid, sid_price=sid_price)

    def total_sid_price(self) -> int:
        total_price = 0
        # for ansector in SchemaTreeIterator(self) is one off (price(SID(0)) == 1)
        for child in self.children:
            for descendant in SchemaTreeIterator(child):
                price = descendant.get_price()
                if price is not None:
                    total_price += price

        return total_price
    # _augment_stmt works without overriding, the Structure is derived from yangson.schemanode.Structure

class DataNode(yangson.schemanode.DataNode, SchemaNode):
    """Abstract superclass for all data nodes with SIDs."""
    def __init__(self) -> None:
        """Initialize the class instance."""
        super().__init__()
        dbg_logger.debug(f"DataNode __init__() {self.__class__.__name__}")

    def _tree_line(self, no_type: bool = False, ctype: bool = True, sid: bool = False, sid_price: bool = False) -> str:
        """Return the receiver's contribution to tree diagram."""
        return SchemaNode._tree_line(self, no_type, ctype, sid=sid, sid_price=sid_price)

class TerminalNode(yangson.schemanode.TerminalNode, SchemaNode):
    """Abstract superclass for terminal nodes with SIDs in the schema tree."""

    def __init__(self) -> None:
        """Initialize the class instance."""
        super().__init__()
        dbg_logger.debug(f"TerminalNode __init__() {self.__class__.__name__}")

    def _tree_line(self, no_type: bool = False, ctype: bool = False, sid: bool = False, sid_price: bool = False) -> str:
        return super(InternalNode, self)._tree_line(no_type, ctype)

    #def _tree_line(self, no_type: bool = False, ctype: bool = True, sid: bool = False, sid_price: bool = False) -> str:
    #    """Return the receiver's contribution to tree diagram."""
    #    return SchemaNode._tree_line(self, no_type, ctype, sid=sid, sid_price=sid_price)

class ContainerNode(yangson.schemanode.ContainerNode, InternalNode):
    """Container node with SIDs."""

    def __init__(self) -> None:
        """Initialize the class instance."""
        super().__init__()
        dbg_logger.debug(f"ContainerNode __init__() {self.__class__.__name__}")

    def _tree_line(self, no_type: bool = False, ctype: bool = True, sid: bool = False, sid_price: bool = False) -> str:
        """Return the receiver's contribution to tree diagram."""
        return SchemaNode._tree_line(self, no_type, ctype, sid=sid, sid_price=sid_price)

class Structure(yangson.schemanode.Structure, InternalNode):
    """ietf-yang-structure-ext:structure node with SIDs."""

    def __init__(self) -> None:
        """Initialize the class instance."""
        super().__init__()
        dbg_logger.debug(f"Structure __init__() {self.__class__.__name__}")

    def _ascii_tree(self, indent: str, no_types: bool, val_count: bool, ctype: bool = True, sid: bool = False, sid_price: bool = False) -> str:
        """Return the receiver's subtree as ASCII art."""

        def suffix(sn):
            return f" {{{sn.val_count}}}" if val_count else "\n"
        if not self.children:
            return ""
        cs = []
        for c in self.children:
            cs.extend(c._flatten())
        res = ""
        for c in cs[:-1]:
            res += (indent + c._tree_line(no_types, False, sid=sid, sid_price=sid_price) + suffix(c) +
                    c._ascii_tree(indent + "|  ", no_types, val_count, False, sid=sid, sid_price=sid_price))
        return (res + indent + cs[-1]._tree_line(no_types, False, sid=sid, sid_price=sid_price) + suffix(cs[-1]) +
                cs[-1]._ascii_tree(indent + "   ", no_types, val_count, False, sid=sid, sid_price=sid_price))

    def _tree_line(self, no_type: bool = False, ctype: bool = True, sid: bool = False, sid_price: bool = False) -> str:
        """Return the receiver's contribution to tree diagram."""
        return SchemaNode._tree_line(self, no_type, ctype, sid=sid, sid_price=sid_price)


class SequenceNode(yangson.schemanode.SequenceNode, SchemaNode):
    """Abstract class for data nodes with SIDs that represent a sequence."""

    def __init__(self) -> None:
        """Initialize the class instance."""
        super().__init__()
        dbg_logger.debug(f"SequenceNode __init__() {self.__class__.__name__}")

    def _tree_line(self, no_type: bool = False, ctype: bool = True, sid: bool = False, sid_price: bool = False) -> str:
        """Return the receiver's contribution to tree diagram."""
        return SchemaNode._tree_line(self, no_type, ctype, sid=sid, sid_price=sid_price)

class ListNode(yangson.schemanode.ListNode, InternalNode):
    """List node with SIDs."""

    def __init__(self) -> None:
        """Initialize the class instance."""
        super().__init__()
        dbg_logger.debug(f"ListNode __init__() {self.__class__.__name__}")

    def _ascii_tree(self, indent: str, no_types: bool, val_count: bool, ctype: bool = True, sid: bool = False, sid_price: bool = False) -> str:
        """Return the receiver's subtree as ASCII art."""
        return InternalNode._ascii_tree(self, indent, no_types, val_count, ctype, sid=sid, sid_price=sid_price)

    def _tree_line(self, no_type: bool = False, ctype: bool = True, sid: bool = False, sid_price: bool = False) -> str:
        """Return the receiver's contribution to tree diagram."""
        return SchemaNode._tree_line(self, no_type, ctype, sid=sid, sid_price=sid_price)

class ChoiceNode(yangson.schemanode.ChoiceNode, InternalNode):
    """Choice node with SIDs."""

    def __init__(self) -> None:
        """Initialize the class instance."""
        super().__init__()
        dbg_logger.debug(f"ChoicoeNode __init__() {self.__class__.__name__}")

    def _handle_child(self, node: yangson.schemanode.SchemaNode, stmt: Statement,
                      sctx: SchemaContext) -> None:
        if isinstance(node, yangson.schemanode.CaseNode):
            super()._handle_child(node, stmt, sctx)
        else:
            cn = CaseNode()
            cn.name = stmt.argument
            cn.ns = sctx.default_ns
            self._add_child(cn)
            cn._handle_child(node, stmt, sctx)

    def has_complete_sid_map(self) -> bool:
        for child in self.children:
            if not child.has_complete_sid_map():
                return False

    def get_price(self) -> Optional[int]:
        return None

    def _ascii_tree(self, indent: str, no_types: bool, val_count: bool, ctype: bool = True, sid: bool = False, sid_price: bool = False) -> str:
        """Return the receiver's subtree as ASCII art."""
        return InternalNode._ascii_tree(self, indent, no_types, val_count, ctype, sid=sid, sid_price=sid_price)

    def _tree_line(self, no_type: bool = False, ctype: bool = True, sid: bool = False, sid_price: bool = False) -> str:
        """Return the receiver's contribution to tree diagram."""
        return InternalNode._tree_line(self, no_type, ctype, sid=sid, sid_price=sid_price)

class CaseNode(yangson.schemanode.CaseNode, InternalNode):
    """Case node with SIDs."""

    def __init__(self) -> None:
        super().__init__()
        dbg_logger.debug(f"CaseNode __init__() {self.__class__.__name__}")

    def has_complete_sid_map(self) -> bool:
        for child in self.children:
            if not child.has_complete_sid_map():
                return False

    def get_price(self) -> Optional[int]:
        return None

    def _ascii_tree(self, indent: str, no_types: bool, val_count: bool, ctype: bool = True, sid: bool = False, sid_price: bool = False) -> str:
        """Return the receiver's subtree as ASCII art."""
        return InternalNode._ascii_tree(self, indent, no_types, val_count, ctype, sid=sid, sid_price=sid_price)

    def _tree_line(self, no_type: bool = False, ctype: bool = True, sid: bool = False, sid_price: bool = False) -> str:
        """Return the receiver's contribution to tree diagram."""
        return InternalNode._tree_line(self, no_type, ctype, sid=sid, sid_price=sid_price)

class LeafNode(yangson.schemanode.LeafNode, SchemaNode):
    """Leaf node with SIDs."""

    def __init__(self) -> None:
        super().__init__()
        dbg_logger.debug(f"LeafNode __init__() {self.__class__.__name__}")

    def has_complete_sid_map(self) -> bool:
        return self.sid is not None

    def _ascii_tree(self, indent: str, no_types: bool, val_count: bool, ctype: bool = True, sid: bool = False, sid_price: bool = False) -> str:
        """Return the receiver's subtree as ASCII art."""
        return ""

    def _tree_line(self, no_type: bool = False, ctype: bool = True, sid: bool = False, sid_price: bool = False) -> str:
        """Return the receiver's contribution to tree diagram."""
        return SchemaNode._tree_line(self, no_type, ctype, sid=sid, sid_price=sid_price)

class LeafListNode(yangson.schemanode.LeafListNode, SchemaNode):
    """Leaf-list node with SIDs."""
    def __init__(self) -> None:
        super().__init__()
        dbg_logger.debug(f"LeafListNode __init__() {self.__class__.__name__}")

    def has_complete_sid_map(self) -> bool:
        return self.sid is not None

    def _ascii_tree(self, indent: str, no_types: bool, val_count: bool, ctype: bool = True, sid: bool = False, sid_price: bool = False) -> str:
        """Return the receiver's subtree as ASCII art."""
        return ""

    def _tree_line(self, no_type: bool = False, ctype: bool = True, sid: bool = False, sid_price: bool = False) -> str:
        """Return the receiver's contribution to tree diagram."""
        return SchemaNode._tree_line(self, no_type, ctype, sid=sid, sid_price=sid_price)
 
class AnyContentNode(yangson.schemanode.AnyContentNode, SchemaNode):
    """Abstract class for anydata or anyxml nodes with SIDs."""

    def __init__(self) -> None:
        super().__init__()
        dbg_logger.debug(f"AnyContentNode __init__() {self.__class__.__name__}")

    def _ascii_tree(self, indent: str, no_types: bool, val_count: bool, ctype: bool = True, sid: bool = False, sid_price: bool = False) -> str:
        """Return the receiver's subtree as ASCII art."""
        return ""

    def _tree_line(self, no_type: bool = False, ctype: bool = True, sid: bool = False, sid_price: bool = False) -> str:
        """Return the receiver's contribution to tree diagram."""
        return SchemaNode._tree_line(self, no_type, ctype, sid=sid, sid_price=sid_price)

class AnydataNode(yangson.schemanode.AnydataNode, SchemaNode):
    """Anydata node with SIDs."""

    def __init__(self) -> None:
        super().__init__()
        dbg_logger.debug(f"AnydataNode __init__() {self.__class__.__name__}")

    def _ascii_tree(self, indent: str, no_types: bool, val_count: bool, ctype: bool = True, sid: bool = False, sid_price: bool = False) -> str:
        """Return the receiver's subtree as ASCII art."""
        return ""

    def _tree_line(self, no_type: bool = False, ctype: bool = True, sid: bool = False, sid_price: bool = False) -> str:
        """Return the receiver's contribution to tree diagram."""
        return SchemaNode._tree_line(self, no_type, ctype, sid=sid, sid_price=sid_price)

class AnyxmlNode(yangson.schemanode.AnyxmlNode, SchemaNode):
    """Anyxml node with SIDs."""

    def __init__(self) -> None:
        super().__init__()
        dbg_logger.debug(f"AnyxmlNode __init__() {self.__class__.__name__}")

    def _ascii_tree(self, indent: str, no_types: bool, val_count: bool, ctype: bool = True, sid: bool = False, sid_price: bool = False) -> str:
        """Return the receiver's subtree as ASCII art."""
        return ""

    def _tree_line(self, no_type: bool = False, ctype: bool = True, sid: bool = False, sid_price: bool = False) -> str:
        """Return the receiver's contribution to tree diagram."""
        return SchemaNode._tree_line(self, no_type, ctype, sid=sid, sid_price=sid_price)

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
        # skip the yangson.schemanode.RpcActionNode._handle_substatements()
        super(yangson.schemanode.SchemaTreeNode, self)._handle_substatements(stmt, sctx)

    def get_price(self) -> Optional[int]:
        return self._absolute_price(self.sid) if self.sid is not None else None

    def _ascii_tree(self, indent: str, no_types: bool, val_count: bool, ctype: bool = True, sid: bool = False, sid_price: bool = False) -> str:
        """Return the receiver's subtree as ASCII art."""
        return InternalNode._ascii_tree(self, indent, no_types, val_count, ctype, sid=sid, sid_price=sid_price)

    def _tree_line(self, no_type: bool = False, ctype: bool = True, sid: bool = False, sid_price: bool = False) -> str:
        """Return the receiver's contribution to tree diagram."""
        return SchemaNode._tree_line(self, no_type, ctype, sid=sid, sid_price=sid_price)

class InputNode(yangson.schemanode.InputNode, InternalNode):
    """RPC or action input node with SIDs."""
    def __init__(self, ns) -> None:
        super().__init__(ns)
        dbg_logger.debug(f"InputNode __init__() {self.__class__.__name__}")

    def _ascii_tree(self, indent: str, no_types: bool, val_count: bool, ctype: bool = True, sid: bool = False, sid_price: bool = False) -> str:
        """Return the receiver's subtree as ASCII art."""
        return InternalNode._ascii_tree(self, indent, no_types, val_count, ctype, sid=sid, sid_price=sid_price)

    def _tree_line(self, no_type: bool = False, ctype: bool = True, sid: bool = False, sid_price: bool = False) -> str:
        """Return the receiver's contribution to tree diagram."""
        return SchemaNode._tree_line(self, no_type, ctype, sid=sid, sid_price=sid_price)

class OutputNode(yangson.schemanode.OutputNode, InternalNode):
    """RPC or action output node with SIDs."""

    def __init__(self, ns) -> None:
        super().__init__(ns)
        dbg_logger.debug(f"OutputNode __init__() {self.__class__.__name__}")

    def _ascii_tree(self, indent: str, no_types: bool, val_count: bool, ctype: bool = True, sid: bool = False, sid_price: bool = False) -> str:
        """Return the receiver's subtree as ASCII art."""
        return InternalNode._ascii_tree(self, indent, no_types, val_count, ctype, sid=sid, sid_price=sid_price)

    def _tree_line(self, no_type: bool = False, ctype: bool = True, sid: bool = False, sid_price: bool = False) -> str:
        """Return the receiver's contribution to tree diagram."""
        return SchemaNode._tree_line(self, no_type, ctype, sid=sid, sid_price=sid_price)

class NotificationNode(yangson.schemanode.NotificationNode, GroupNode):
    """Notification node with SIDs."""

    def __init__(self) -> None:
        super().__init__()
        dbg_logger.debug(f"NotificationNode __init__() {self.__class__.__name__}")

    def get_price(self) -> Optional[int]:
        return self._absolute_price(self.sid) if self.sid is not None else None

    def _ascii_tree(self, indent: str, no_types: bool, val_count: bool, ctype: bool = True, sid: bool = False, sid_price: bool = False) -> str:
        """Return the receiver's subtree as ASCII art."""
        return InternalNode._ascii_tree(self, indent, no_types, val_count, ctype, sid=sid, sid_price=sid_price)

    def _tree_line(self, no_type: bool = False, ctype: bool = True, sid: bool = False, sid_price: bool = False) -> str:
        """Return the receiver's contribution to tree diagram."""
        return SchemaNode._tree_line(self, no_type, ctype, sid=sid, sid_price=sid_price)
 
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


class SchemaTreeIterator:
    def __init__(self, node: SchemaNode) -> None:
        self.current: optional[SchemaNode] = node
        self.stack: list[InternalNode] = []

    def __iter__(self) -> Iterator[SchemaNode]:
        return self

    def __next__(self) -> SchemaNode:
        if self.current is None:
            raise StopIteration()

        node: SchemaNode = self.current
        to_return: SchemaNode = self.current
        if isinstance(node, InternalNode) and len(node.children) > 0:
            self.stack.append(node)
            self.current = node.children[0]
            return to_return

        while len(self.stack) > 0:
            last = node
            node = self.stack[-1]

            try:
                # will never throw a valueerror
                i = node.children.index(last)

                if i + 1 < len(node.children):
                    self.current = node.children[i + 1]
                    return to_return

                node = self.stack.pop()

            except valueerror:
                assert false

        self.current = None
        return to_return
