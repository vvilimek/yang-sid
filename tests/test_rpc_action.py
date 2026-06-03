# SPDX-FileCopyrightText: CZ.NIC z.s.p.o.
#
# SPDX-License-Identifier: LGPL-3.0-or-later

import yang_sid
import pytest

from yang_sid_base import SID

from pathlib import Path

"""
Test desciption


"""

MOD_PATH = (Path(yang_sid.__file__).parent.parent.parent / "yang_modules", Path(yang_sid.__file__).parent / "yang_modules")
SID_PATH = Path(yang_sid.__file__).parent.parent.parent / "sid"

YANG_LIB = """
{
  "ietf-yang-library:modules-state": {
    "module": [
      {
        "name": "a",
        "revision": "2026-04-03",
        "namespace": "http://example.com/a/main",
        "feature": [],
        "submodule": [
          {
            "name": "a-sub",
            "revision": "2026-04-03"
          }
        ],
        "conformance-type": "implement"
      },
      {
        "name": "b",
        "revision": "2026-04-01",
        "namespace": "http://example.com/b/",
        "conformance-type": "implement"
      },
      {
        "name": "c",
        "revision": "2026-04-02",
        "namespace": "http://example.com/c/",
        "feature": [],
        "conformance-type": "import"
      },
      {
        "name": "ietf-inet-types",
        "revision": "2025-12-22",
        "namespace": "urn:ietf:params:xml:ns:yang:ietf-inet-types",
        "conformance-type": "implement"
      },
      {
        "name": "ietf-yang-types",
        "revision": "2025-12-22",
        "namespace": "urn:ietf:params:xml:ns:yang:ietf-yang-types",
        "conformance-type": "implement"
      }
    ],
    "module-set-id": "0"
  }
}
"""

@pytest.fixture
def data_model():
    model = yang_sid.DataModel(YANG_LIB, mod_path=MOD_PATH)
    model.set_sid_path([SID_PATH])
    model.load_all_module_sids()
    return model

def test_mod_a_rpc(data_model):
    schema_data = data_model.schema_data
    schema = data_model.schema

    id = "/a:reset"
    route = schema_data.path2route(id)
    node = schema.get_schema_descendant(route)
    assert node.sid == SID(61059)
    assert schema_data.all_sids[SID(61059)] is node
    inp = node.get_schema_descendant([("input", "a")])
    assert inp.sid == SID(61060)
    assert schema_data.all_sids[SID(61060)] is inp
    outp = node.get_schema_descendant([("output", "a")])
    assert outp.sid == SID(61061)
    assert schema_data.all_sids[SID(61061)] is outp
    assert node.children_by_sid == {SID(61060): inp, SID(61061): outp}

    id = "/a:cas-date"
    route = schema_data.path2route(id)
    node = schema.get_schema_descendant(route)
    assert node.sid == SID(61043)
    assert schema_data.all_sids[SID(61043)] is node

    inp = node.get_schema_descendant([("input", "a")])
    assert inp.sid == SID(61044)
    assert schema_data.all_sids[SID(61044)] is inp
    outp = node.get_schema_descendant([("output", "a")])
    assert outp.sid == SID(61047)
    assert schema_data.all_sids[SID(61047)] is outp

    in_expect = inp.get_schema_descendant([("expected" ,"a")])
    assert in_expect.sid == SID(61045)
    assert schema_data.all_sids[SID(61045)] is in_expect
    assert inp.children_by_sid == {
            SID(61045): in_expect,
            SID(61046): inp.get_schema_descendant([("new-value", "a")])
            }

    out_old_curr = outp.get_schema_descendant([("old-or-current", "a")])
    assert out_old_curr.sid == SID(61048)
    assert schema_data.all_sids[SID(61048)] is out_old_curr
    assert outp.children_by_sid == {SID(61048): out_old_curr}

    assert node.children_by_sid == {SID(61044): inp, SID(61047): outp}


def test_mod_a_action(data_model):
    schema_data = data_model.schema_data
    schema = data_model.schema

    id = "/a:box/ips/add"
    route = schema_data.path2route(id)
    node = schema.get_schema_descendant(route)
    assert node.sid == SID(61016)
    assert schema_data.all_sids[SID(61016)] is node

    inp = node.get_schema_descendant([("input", "a")])
    assert inp.sid == SID(61017)
    assert schema_data.all_sids[SID(61017)] is inp

    outp = node.get_schema_descendant([("output", "a")])
    assert outp.sid == SID(61020)
    assert schema_data.all_sids[SID(61020)] is outp

    assert node.children_by_sid == {
                SID(61017): inp,
                SID(61020): outp,
            }

    id = "/a:box/ips/ips/remove"
    route = schema_data.path2route(id)
    node = schema.get_schema_descendant(route)
    assert node.sid == SID(61025)
    assert schema_data.all_sids[SID(61025)] is node

    inp = node.get_schema_descendant([("input", "a")])
    assert inp.sid == SID(61026)
    assert schema_data.all_sids[SID(61026)] == inp

    outp = node.get_schema_descendant([("output", "a")])
    assert outp.sid == SID(61028)
    assert schema_data.all_sids[SID(61028)] == outp

    assert node.children_by_sid == {
            SID(61026): inp,
            SID(61028): outp,
            }

# no rpcs, actions in ietf-yang-types, ietf-inet-types

