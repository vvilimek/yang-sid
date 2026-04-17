# SPDX-FileCopyrightText: CZ.NIC z.s.p.o.
#
# SPDX-License-Identifier: LGPL-3.0-or-later

import yang_sid
import pytest

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
    assert node.sid == 61056
    assert schema_data.all_sids[61056] is node
    inp = node.get_schema_descendant([("input", "a")])
    assert inp.sid == 61057
    assert schema_data.all_sids[61057] is inp
    outp = node.get_schema_descendant([("output", "a")])
    assert outp.sid == 61058
    assert schema_data.all_sids[61058] is outp
    assert node.children_by_sid == {61057: inp, 61058: outp}

    id = "/a:cas-date"
    route = schema_data.path2route(id)
    node = schema.get_schema_descendant(route)
    assert node.sid == 61040
    assert schema_data.all_sids[61040] is node

    inp = node.get_schema_descendant([("input", "a")])
    assert inp.sid == 61041
    assert schema_data.all_sids[61041] is inp
    outp = node.get_schema_descendant([("output", "a")])
    assert outp.sid == 61044
    assert schema_data.all_sids[61044] is outp

    in_expect = inp.get_schema_descendant([("expected" ,"a")])
    assert in_expect.sid == 61042
    assert schema_data.all_sids[61042] is in_expect
    assert inp.children_by_sid == {
            61042: in_expect,
            61043: inp.get_schema_descendant([("new-value", "a")])
            }

    out_old_curr = outp.get_schema_descendant([("old-or-current", "a")])
    assert out_old_curr.sid == 61045
    assert schema_data.all_sids[61045] is out_old_curr
    assert outp.children_by_sid == {61045: out_old_curr}
    
    assert node.children_by_sid == {61041: inp, 61044: outp}


def test_mod_a_action(data_model):
    schema_data = data_model.schema_data
    schema = data_model.schema

    id = "/a:box/ips/add"
    route = schema_data.path2route(id)
    node = schema.get_schema_descendant(route)
    assert node.sid == 61016
    assert schema_data.all_sids[61016] is node

    inp = node.get_schema_descendant([("input", "a")])
    assert inp.sid == 61017
    assert schema_data.all_sids[61017] is inp

    outp = node.get_schema_descendant([("output", "a")])
    assert outp.sid == 61020
    assert schema_data.all_sids[61020] is outp

    assert node.children_by_sid == {
                61017: inp, 
                61020: outp,
            }

    id = "/a:box/ips/ips/remove"
    route = schema_data.path2route(id)
    node = schema.get_schema_descendant(route)
    assert node.sid == 61025
    assert schema_data.all_sids[61025] is node 

    inp = node.get_schema_descendant([("input", "a")])
    assert inp.sid == 61026
    assert schema_data.all_sids[61026] == inp

    outp = node.get_schema_descendant([("output", "a")])
    assert outp.sid == 61028
    assert schema_data.all_sids[61028] == outp

    assert node.children_by_sid == {
            61026: inp,
            61028: outp,
            }

# no rpcs, actions in ietf-yang-types, ietf-inet-types

