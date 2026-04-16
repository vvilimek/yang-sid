# SPDX-FileCopyrightText: CZ.NIC z.s.p.o.
#
# SPDX-License-Identifier: LGPL-3.0-or-later


import logging
import copy

import yangson.schemanode
import yangson.datatype
from yangson.statement import Statement
from yangson.schemadata import SchemaContext

from .types import SID
from .sid_file import SidFile, ItemNamespace

from typing import Optional

dbg_logger = logging.getLogger("yang_sid.schema INIT")
dbg_logger.setLevel(logging.DEBUG)

logger = logging.getLogger(__name__)

class SchemaNode(yangson.schemanode.SchemaNode):
    def __init__(self) -> None:
        super().__init__()
        self.sid: Optional[SID] = None
        dbg_logger.debug(f"SchemaNode __init__() {self.__class__.__name__}")

    # _follow_leafref  works without overriding, the YangData is derived from yangson.schemanode.YangData

class InternalNode(yangson.schemanode.InternalNode, SchemaNode):
    def __init__(self) -> None:
        super().__init__()
        self.children_by_sid: dict[SID, SchemaNode] = {}
        dbg_logger.debug(f"InternalNode __init__() {self.__class__.__name__}")

    def _anydata_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        self._handle_child(AnydataNode(), stmt, sctx)

    def _anyxml_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        self._handle_child(AnyxmlNode(), stmt, sctx)

    def _case_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        self._handle_child(CaseNode(), stmt, sctx)

    def _choice_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        self._handle_child(ChoiceNode(), stmt, sctx)

    def _container_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        self._handle_child(ContainerNode(), stmt, sctx)

    def _leaf_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        node = LeafNode()
        node.type = yangson.datatype.DataType._resolve_type(
                stmt.find1("type", required=True), sctx)
        self._handle_child(node, stmt, sctx)

    def _leaf_list_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        node = LeafListNode()
        node.type = yangson.datatype.DataType._resolve_type(
                stmt.find1("type", required=True), sctx)
        self._handle_child(node, stmt, sctx)

    def _list_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        self._handle_child(ListNode(), stmt, sctx)

    def _notification_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        self._handle_child(NotificationNode(), stmt, sctx)

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


    # _schema_pattern works without overriding, the YangData is derived from yangson.schemanode.YangData
    # _handle_child works without overriding, the YangData is derived from yangson.schemanode.YangData
    # _augment_stmt works without overriding, both YangData and Structure are derived from yangson.schemanode.YangData, resp. yangson.schemanode.Structure
    # _ascii_tree works without overriding, both YangData and Structure are derived from yangson.schemanode.YangData, resp. yangson.schemanode.Structure
    # _refind_stmt works without overriding, the YangData is derived from yangson.schemanode.YangData
    # _uses_stmt works without overriding, the YangData is derived from yangson.schemanode.YangData
    # _identity_stmt works without overriding, the YangData is derived from yangson.schemanode.YangData
    # _ascii_tree works without overriding, both YangData and Structure are derived from yangson.schemanode.YangData, resp. yangson.schemanode.Structure


class GroupNode(yangson.schemanode.GroupNode, InternalNode):
    def __init__(self) -> None:
        super().__init__()
        dbg_logger.debug(f"GroupNode __init__() {self.__class__.__name__}")

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

    def _anydata_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        InternalNode._anydata_stmt(self, stmt, sctx)

    def _anyxml_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        InternalNode._anyxml_stmt(self, stmt, sctx)

    def _case_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        InternalNode._case_stmt(self, stmt, sctx)

    def _choice_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        InternalNode._choice_stmt(self, stmt, sctx)

    def _container_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        InternalNode._container_stmt(self, stmt, sctx)

    def _input_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        InternalNode._input_stmt(self, stmt, sctx)

    def _leaf_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        InternalNode._leaf_stmt(self, stmt, sctx)

    def _leaf_list_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        InternalNode._leaf_list_stmt(self, stmt, sctx)

    def _list_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        InternalNode._list_stmt(self, stmt, sctx)

    def _notification_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        InternalNode._notification_stmt(self, stmt, sctx)

    def _output_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        InternalNode._output_stmt(self, stmt, sctx)

    def _rpc_action_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        InternalNode._rpc_action_stmt(self, stmt, sctx)

    def _augment_stmt(self, stmt: Statement,
                      sctx: SchemaContext) -> None:
        InternalNode._augment_stmt(self, stmt, sctx)

    def _uses_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        InternalNode._uses_stmt(self, stmt, sctx)

    def _sx_structure_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        InternalNode._sx_structure_stmt(self, stmt, sctx)

    def _rc_yang_data_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        InternalNode._rc_yang_data_stmt(self, stmt, sctx)

    def _handle_child(self, node: yangson.schemanode.SchemaNode, stmt: Statement,
                      sctx: SchemaContext) -> None:
        InternalNode._handle_child(self, node, stmt, sctx)


class YangData(yangson.schemanode.YangData, GroupNode):
    def __init__(self, sctx: Optional[SchemaContext] = None) -> None:
        super().__init__(sctx)
        dbg_logger.debug(f"YangData __init__() {self.__class__.__name__}")

    def _anydata_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        GroupNode._anydata_stmt(self, stmt, sctx)

    def _anyxml_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        GroupNode._anyxml_stmt(self, stmt, sctx)

    def _case_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        GroupNode._case_stmt(self, stmt, sctx)

    def _choice_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        GroupNode._choice_stmt(self, stmt, sctx)

    def _container_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        GroupNode._container_stmt(self, stmt, sctx)

    def _input_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        GroupNode._input_stmt(self, stmt, sctx)

    def _leaf_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        GroupNode._leaf_stmt(self, stmt, sctx)

    def _leaf_list_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        GroupNode._leaf_list_stmt(self, stmt, sctx)

    def _list_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        GroupNode._list_stmt(self, stmt, sctx)

    def _notification_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        GroupNode._notification_stmt(self, stmt, sctx)

    def _output_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        GroupNode._output_stmt(self, stmt, sctx)

    def _rpc_action_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        GroupNode._rpc_action_stmt(self, stmt, sctx)

    def _sx_structure_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        InternalNode._sx_structure_stmt(self, stmt, sctx)

    def _rc_yang_data_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        InternalNode._rc_yang_data_stmt(self, stmt, sctx)

    def _augment_stmt(self, stmt: Statement,
                      sctx: SchemaContext) -> None:
        GroupNode._augment_stmt(self, stmt, sctx)

    def _uses_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        GroupNode._uses_stmt(self, stmt, sctx)

    def _handle_child(self, node: yangson.schemanode.SchemaNode, stmt: Statement,
                      sctx: SchemaContext) -> None:
        GroupNode._handle_child(self, node, stmt, sctx)

class SchemaTreeNode(yangson.schemanode.SchemaTreeNode, GroupNode):
    def __init__(self, schemadata: Optional[yangson.schemadata.SchemaData] = None):
        super().__init__(schemadata)
        dbg_logger.debug(f"SchemaTreeNode __init__() {self.__class__.__name__}")

    def apply_sid_file(self, sid_file: SidFile) -> None:
        for item in sid_file.item.values():
            if item.namespace != ItemNamespace.DATA:
                continue

            # TODO: Test RPC, ACTION, NOTIFICATION, YANG_DATA, SX_STRUCTURE
            route = self.schema_data.path2route(item.identifier)
            node = self.get_schema_descendant(route)
            if node:
                node.sid = item.sid
                self.schema_data.all_sids[item.sid] = node
                if node.parent:
                    node.parent.children_by_sid[item.sid] = node
            else:
                logger.warning(f"Unsupported node identified by {item.identifier}")

    def _anydata_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        GroupNode._anydata_stmt(self, stmt, sctx)

    def _anyxml_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        GroupNode._anyxml_stmt(self, stmt, sctx)

    def _case_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        GroupNode._case_stmt(self, stmt, sctx)

    def _choice_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        GroupNode._choice_stmt(self, stmt, sctx)

    def _container_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        GroupNode._container_stmt(self, stmt, sctx)

    def _input_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        GroupNode._input_stmt(self, stmt, sctx)

    def _leaf_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        GroupNode._leaf_stmt(self, stmt, sctx)

    def _leaf_list_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        GroupNode._leaf_list_stmt(self, stmt, sctx)

    def _list_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        GroupNode._list_stmt(self, stmt, sctx)

    def _notification_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        GroupNode._notification_stmt(self, stmt, sctx)

    def _output_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        GroupNode._output_stmt(self, stmt, sctx)

    def _rpc_action_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        GroupNode._rpc_action_stmt(self, stmt, sctx)
    def _sx_structure_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:

        InternalNode._sx_structure_stmt(self, stmt, sctx)

    def _rc_yang_data_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        InternalNode._rc_yang_data_stmt(self, stmt, sctx)

    def _augment_stmt(self, stmt: Statement,
                      sctx: SchemaContext) -> None:
        GroupNode._augment_stmt(self, stmt, sctx)

    def _uses_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        GroupNode._uses_stmt(self, stmt, sctx)

    def _handle_child(self, node: yangson.schemanode.SchemaNode, stmt: Statement,
                      sctx: SchemaContext) -> None:
        GroupNode._handle_child(self, node, stmt, sctx)

    def _sx_structure_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        struct = Structure()
        self._handle_child(struct, stmt, sctx)

    def _rc_yang_data_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        """Handle the ietf-restconf:yang-data statement."""
        yd_sch_data = copy.copy(sctx.schema_data)
        # We cannot afford to use SchemaData constructor as it requires YANG Library as dict
        sd = sctx.schema_data
        main_mod: ModuleData = sd.modules[sctx.text_mid]
        accessible_mods: list[ModuleId] = []
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

    # _augment_stmt works without overriding, the Structure is derived from yangson.schemanode.Structure

class DataNode(yangson.schemanode.DataNode, SchemaNode):
    def __init__(self) -> None:
        super().__init__()
        dbg_logger.debug(f"DataNode __init__() {self.__class__.__name__}")

class TerminalNode(yangson.schemanode.TerminalNode, SchemaNode):
    def __init__(self) -> None:
        super().__init__()
        dbg_logger.debug(f"TerminalNode __init__() {self.__class__.__name__}")

class ContainerNode(yangson.schemanode.ContainerNode, InternalNode):
    def __init__(self) -> None:
        super().__init__()
        dbg_logger.debug(f"ContainerNode __init__() {self.__class__.__name__}")

    def _anydata_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        InternalNode._anydata_stmt(self, stmt, sctx)

    def _anyxml_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        InternalNode._anyxml_stmt(self, stmt, sctx)

    def _case_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        InternalNode._case_stmt(self, stmt, sctx)

    def _choice_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        InternalNode._choice_stmt(self, stmt, sctx)

    def _container_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        InternalNode._container_stmt(self, stmt, sctx)

    def _input_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        InternalNode._input_stmt(self, stmt, sctx)

    def _leaf_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        InternalNode._leaf_stmt(self, stmt, sctx)

    def _leaf_list_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        InternalNode._leaf_list_stmt(self, stmt, sctx)

    def _list_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        InternalNode._list_stmt(self, stmt, sctx)

    def _notification_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        InternalNode._notification_stmt(self, stmt, sctx)

    def _output_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        InternalNode._output_stmt(self, stmt, sctx)

    def _rpc_action_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        InternalNode._rpc_action_stmt(self, stmt, sctx)

    def _sx_structure_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        InternalNode._sx_structure_stmt(self, stmt, sctx)

    def _rc_yang_data_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        InternalNode._rc_yang_data_stmt(self, stmt, sctx)

    def _augment_stmt(self, stmt: Statement,
                      sctx: SchemaContext) -> None:
        InternalNode._augment_stmt(self, stmt, sctx)

    def _uses_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        InternalNode._uses_stmt(self, stmt, sctx)


class Structure(yangson.schemanode.Structure, InternalNode):
    def __init__(self) -> None:
        super().__init__()
        dbg_logger.debug(f"Structure __init__() {self.__class__.__name__}")

    def _anydata_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        InternalNode._anydata_stmt(self, stmt, sctx)

    def _anyxml_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        InternalNode._anyxml_stmt(self, stmt, sctx)

    def _case_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        InternalNode._case_stmt(self, stmt, sctx)

    def _choice_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        InternalNode._choice_stmt(self, stmt, sctx)

    def _container_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        InternalNode._container_stmt(self, stmt, sctx)

    def _input_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        InternalNode._input_stmt(self, stmt, sctx)

    def _leaf_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        InternalNode._leaf_stmt(self, stmt, sctx)

    def _leaf_list_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        InternalNode._leaf_list_stmt(self, stmt, sctx)

    def _list_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        InternalNode._list_stmt(self, stmt, sctx)

    def _notification_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        InternalNode._notification_stmt(self, stmt, sctx)

    def _output_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        InternalNode._output_stmt(self, stmt, sctx)

    def _rpc_action_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        InternalNode._rpc_action_stmt(self, stmt, sctx)

    def _sx_structure_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        InternalNode._sx_structure_stmt(self, stmt, sctx)

    def _rc_yang_data_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        InternalNode._rc_yang_data_stmt(self, stmt, sctx)

    def _augment_stmt(self, stmt: Statement,
                      sctx: SchemaContext) -> None:
        InternalNode._augment_stmt(self, stmt, sctx)

    def _uses_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        InternalNode._uses_stmt(self, stmt, sctx)


class SequenceNode(yangson.schemanode.SequenceNode, SchemaNode):
    def __init__(self) -> None:
        super().__init__()
        dbg_logger.debug(f"SequenceNode __init__() {self.__class__.__name__}")

class ListNode(yangson.schemanode.ListNode, InternalNode):
    def __init__(self) -> None:
        super().__init__()
        dbg_logger.debug(f"ListNode __init__() {self.__class__.__name__}")

    def _anydata_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        InternalNode._anydata_stmt(self, stmt, sctx)

    def _anyxml_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        InternalNode._anyxml_stmt(self, stmt, sctx)

    def _case_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        InternalNode._case_stmt(self, stmt, sctx)

    def _choice_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        InternalNode._choice_stmt(self, stmt, sctx)

    def _container_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        InternalNode._container_stmt(self, stmt, sctx)

    def _input_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        InternalNode._input_stmt(self, stmt, sctx)

    def _leaf_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        InternalNode._leaf_stmt(self, stmt, sctx)

    def _leaf_list_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        InternalNode._leaf_list_stmt(self, stmt, sctx)

    def _list_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        InternalNode._list_stmt(self, stmt, sctx)

    def _notification_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        InternalNode._notification_stmt(self, stmt, sctx)

    def _output_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        InternalNode._output_stmt(self, stmt, sctx)

    def _rpc_action_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        InternalNode._rpc_action_stmt(self, stmt, sctx)

    def _sx_structure_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        InternalNode._sx_structure_stmt(self, stmt, sctx)

    def _rc_yang_data_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        InternalNode._rc_yang_data_stmt(self, stmt, sctx)

    def _augment_stmt(self, stmt: Statement,
                      sctx: SchemaContext) -> None:
        InternalNode._augment_stmt(self, stmt, sctx)

    def _uses_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        InternalNode._uses_stmt(self, stmt, sctx)


class ChoiceNode(yangson.schemanode.ChoiceNode, InternalNode):
    def __init__(self) -> None:
        super().__init__()
        dbg_logger.debug(f"ChoicoeNode __init__() {self.__class__.__name__}")

    def _anydata_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        InternalNode._anydata_stmt(self, stmt, sctx)

    def _anyxml_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        InternalNode._anyxml_stmt(self, stmt, sctx)

    def _case_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        InternalNode._case_stmt(self, stmt, sctx)

    def _choice_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        InternalNode._choice_stmt(self, stmt, sctx)

    def _container_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        InternalNode._container_stmt(self, stmt, sctx)

    def _input_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        InternalNode._input_stmt(self, stmt, sctx)

    def _leaf_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        InternalNode._leaf_stmt(self, stmt, sctx)

    def _leaf_list_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        InternalNode._leaf_list_stmt(self, stmt, sctx)

    def _list_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        InternalNode._list_stmt(self, stmt, sctx)

    def _notification_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        InternalNode._notification_stmt(self, stmt, sctx)

    def _output_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        InternalNode._output_stmt(self, stmt, sctx)

    def _rpc_action_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        InternalNode._rpc_action_stmt(self, stmt, sctx)

    def _sx_structure_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        InternalNode._sx_structure_stmt(self, stmt, sctx)

    def _rc_yang_data_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        InternalNode._rc_yang_data_stmt(self, stmt, sctx)

    def _augment_stmt(self, stmt: Statement,
                      sctx: SchemaContext) -> None:
        InternalNode._augment_stmt(self, stmt, sctx)

    def _uses_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        InternalNode._uses_stmt(self, stmt, sctx)

class CaseNode(yangson.schemanode.CaseNode, InternalNode):
    def __init__(self) -> None:
        super().__init__()
        dbg_logger.debug(f"CaseNode __init__() {self.__class__.__name__}")
    def _anydata_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        InternalNode._anydata_stmt(self, stmt, sctx)

    def _anyxml_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        InternalNode._anyxml_stmt(self, stmt, sctx)

    def _case_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        InternalNode._case_stmt(self, stmt, sctx)

    def _choice_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        InternalNode._choice_stmt(self, stmt, sctx)

    def _container_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        InternalNode._container_stmt(self, stmt, sctx)

    def _input_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        InternalNode._input_stmt(self, stmt, sctx)

    def _leaf_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        InternalNode._leaf_stmt(self, stmt, sctx)

    def _leaf_list_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        InternalNode._leaf_list_stmt(self, stmt, sctx)

    def _list_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        InternalNode._list_stmt(self, stmt, sctx)

    def _notification_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        InternalNode._notification_stmt(self, stmt, sctx)

    def _output_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        InternalNode._output_stmt(self, stmt, sctx)

    def _rpc_action_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        InternalNode._rpc_action_stmt(self, stmt, sctx)

    def _sx_structure_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        InternalNode._sx_structure_stmt(self, stmt, sctx)

    def _rc_yang_data_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        InternalNode._rc_yang_data_stmt(self, stmt, sctx)

    def _augment_stmt(self, stmt: Statement,
                      sctx: SchemaContext) -> None:
        InternalNode._augment_stmt(self, stmt, sctx)

    def _uses_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        InternalNode._uses_stmt(self, stmt, sctx)

    def _handle_child(self, node: yangson.schemanode.SchemaNode, stmt: Statement,
                      sctx: SchemaContext) -> None:
        InternalNode._handle_child(self, node, stmt, sctx)

class LeafNode(yangson.schemanode.LeafNode, SchemaNode):
    def __init__(self) -> None:
        super().__init__()
        dbg_logger.debug(f"LeafNode __init__() {self.__class__.__name__}")

class LeafListNode(yangson.schemanode.LeafListNode, SchemaNode):
    def __init__(self) -> None:
        super().__init__()
        dbg_logger.debug(f"LeafListNode __init__() {self.__class__.__name__}")

class AnyContentNode(yangson.schemanode.AnyContentNode, SchemaNode):
    def __init__(self) -> None:
        super().__init__()
        dbg_logger.debug(f"AnyContentNode __init__() {self.__class__.__name__}")

class AnydataNode(yangson.schemanode.AnydataNode, SchemaNode):
    def __init__(self) -> None:
        super().__init__()
        dbg_logger.debug(f"AnydataNode __init__() {self.__class__.__name__}")

class AnyxmlNode(yangson.schemanode.AnyxmlNode, SchemaNode):
    def __init__(self) -> None:
        super().__init__()
        dbg_logger.debug(f"AnyxmlNode __init__() {self.__class__.__name__}")

class RpcActionNode(yangson.schemanode.RpcActionNode, GroupNode):
    def __init__(self) -> None:
        super().__init__()
        dbg_logger.debug(f"RpcActionNode __init__() {self.__class__.__name__}")

    def _anydata_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        GroupNode._anydata_stmt(self, stmt, sctx)

    def _anyxml_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        GroupNode._anyxml_stmt(self, stmt, sctx)

    def _case_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        GroupNode._case_stmt(self, stmt, sctx)

    def _choice_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        GroupNode._choice_stmt(self, stmt, sctx)

    def _container_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        GroupNode._container_stmt(self, stmt, sctx)

    def _input_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        self.get_child("input")._handle_substatements(stmt, sctx)

    def _leaf_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        GroupNode._leaf_stmt(self, stmt, sctx)

    def _leaf_list_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        GroupNode._leaf_list_stmt(self, stmt, sctx)

    def _list_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        GroupNode._list_stmt(self, stmt, sctx)

    def _notification_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        GroupNode._notification_stmt(self, stmt, sctx)

    def _output_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        self.get_child("output")._handle_substatements(stmt, sctx)

    def _rpc_action_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        GroupNode._rpc_action_stmt(self, stmt, sctx)

    def _sx_structure_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        InternalNode._sx_structure_stmt(self, stmt, sctx)

    def _rc_yang_data_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        InternalNode._rc_yang_data_stmt(self, stmt, sctx)

    def _augment_stmt(self, stmt: Statement,
                      sctx: SchemaContext) -> None:
        GroupNode._augment_stmt(self, stmt, sctx)

    def _uses_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        GroupNode._uses_stmt(self, stmt, sctx)

    def _handle_child(self, node: yangson.schemanode.SchemaNode, stmt: Statement,
                      sctx: SchemaContext) -> None:
        GroupNode._handle_child(self, node, stmt, sctx)

    def _handle_substatements(self, stmt: Statement, sctx: SchemaContext) -> None:
        self._add_child(InputNode(sctx.default_ns))
        self._add_child(OutputNode(sctx.default_ns))
        super()._handle_substatements(stmt, sctx)

class InputNode(yangson.schemanode.InputNode, InternalNode):
    def __init__(self, ns) -> None:
        super().__init__(ns)
        dbg_logger.debug(f"InputNode __init__() {self.__class__.__name__}")

    def _anydata_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        InternalNode._anydata_stmt(self, stmt, sctx)

    def _anyxml_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        InternalNode._anyxml_stmt(self, stmt, sctx)

    def _case_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        InternalNode._case_stmt(self, stmt, sctx)

    def _choice_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        InternalNode._choice_stmt(self, stmt, sctx)

    def _container_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        InternalNode._container_stmt(self, stmt, sctx)

    def _input_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        InternalNode._input_stmt(self, stmt, sctx)

    def _leaf_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        InternalNode._leaf_stmt(self, stmt, sctx)

    def _leaf_list_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        InternalNode._leaf_list_stmt(self, stmt, sctx)

    def _list_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        InternalNode._list_stmt(self, stmt, sctx)

    def _notification_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        InternalNode._notification_stmt(self, stmt, sctx)

    def _output_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        InternalNode._output_stmt(self, stmt, sctx)

    def _rpc_action_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        InternalNode._rpc_action_stmt(self, stmt, sctx)

    def _sx_structure_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        InternalNode._sx_structure_stmt(self, stmt, sctx)

    def _rc_yang_data_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        InternalNode._rc_yang_data_stmt(self, stmt, sctx)

    def _augment_stmt(self, stmt: Statement,
                      sctx: SchemaContext) -> None:
        InternalNode._augment_stmt(self, stmt, sctx)

    def _uses_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        InternalNode._uses_stmt(self, stmt, sctx)

class OutputNode(yangson.schemanode.OutputNode, InternalNode):
    def __init__(self, ns) -> None:
        super().__init__(ns)
        dbg_logger.debug(f"OutputNode __init__() {self.__class__.__name__}")

    def _anydata_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        InternalNode._anydata_stmt(self, stmt, sctx)

    def _anyxml_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        InternalNode._anyxml_stmt(self, stmt, sctx)

    def _case_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        InternalNode._case_stmt(self, stmt, sctx)

    def _choice_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        InternalNode._choice_stmt(self, stmt, sctx)

    def _container_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        InternalNode._container_stmt(self, stmt, sctx)

    def _input_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        InternalNode._input_stmt(self, stmt, sctx)

    def _leaf_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        InternalNode._leaf_stmt(self, stmt, sctx)

    def _leaf_list_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        InternalNode._leaf_list_stmt(self, stmt, sctx)

    def _list_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        InternalNode._list_stmt(self, stmt, sctx)

    def _notification_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        InternalNode._notification_stmt(self, stmt, sctx)

    def _output_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        InternalNode._output_stmt(self, stmt, sctx)

    def _rpc_action_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        InternalNode._rpc_action_stmt(self, stmt, sctx)

    def _sx_structure_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        InternalNode._sx_structure_stmt(self, stmt, sctx)

    def _rc_yang_data_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        InternalNode._rc_yang_data_stmt(self, stmt, sctx)

    def _augment_stmt(self, stmt: Statement,
                      sctx: SchemaContext) -> None:
        InternalNode._augment_stmt(self, stmt, sctx)

    def _uses_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        InternalNode._uses_stmt(self, stmt, sctx)

class NotificationNode(yangson.schemanode.NotificationNode, GroupNode):
    def __init__(self) -> None:
        super().__init__()
        dbg_logger.debug(f"NotificationNode __init__() {self.__class__.__name__}")


    def _anydata_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        GroupNode._anydata_stmt(self, stmt, sctx)

    def _anyxml_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        GroupNode._anyxml_stmt(self, stmt, sctx)

    def _case_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        GroupNode._case_stmt(self, stmt, sctx)

    def _choice_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        GroupNode._choice_stmt(self, stmt, sctx)

    def _container_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        GroupNode._container_stmt(self, stmt, sctx)

    def _input_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        GroupNode._input_stmt(self, stmt, sctx)

    def _leaf_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        GroupNode._leaf_stmt(self, stmt, sctx)

    def _leaf_list_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        GroupNode._leaf_list_stmt(self, stmt, sctx)

    def _list_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        GroupNode._list_stmt(self, stmt, sctx)

    def _notification_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        GroupNode._notification_stmt(self, stmt, sctx)

    def _output_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        GroupNode._output_stmt(self, stmt, sctx)

    def _rpc_action_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        GroupNode._rpc_action_stmt(self, stmt, sctx)

    def _sx_structure_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        InternalNode._sx_structure_stmt(self, stmt, sctx)

    def _rc_yang_data_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        InternalNode._rc_yang_data_stmt(self, stmt, sctx)

    def _augment_stmt(self, stmt: Statement,
                      sctx: SchemaContext) -> None:
        GroupNode._augment_stmt(self, stmt, sctx)

    def _uses_stmt(self, stmt: Statement, sctx: SchemaContext) -> None:
        GroupNode._uses_stmt(self, stmt, sctx)

    def _handle_child(self, node: yangson.schemanode.SchemaNode, stmt: Statement,
                      sctx: SchemaContext) -> None:
        GroupNode._handle_child(self, node, stmt, sctx)

class SchemaTreeFactory:
    def create_tree(self, schemadata: yangson.schemadata.SchemaData) -> yangson.schemanode.SchemaTreeNode:
        return SchemaTreeNode(schemadata)



