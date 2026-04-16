import pytest
import yang_sid

from pathlib import Path

MOD_PATH = (Path(yang_sid.__file__).parent.parent.parent / "yang_modules", Path(yang_sid.__file__).parent / "yang_modules")
SID_PATH = Path(yang_sid.__file__).parent.parent.parent / "sid"

YANG_LIB_RFC_EXAMPLE = """
{
  "ietf-yang-library:modules-state": {
    "module": [
      {
        "name": "example-module",
        "revision": "2020-06-17",
        "namespace": "urn:example:example-module",
        "conformance-type": "implement"
      },
      {
        "name": "example-module-aug",
        "revision": "",
        "namespace": "urn:example:example-module-aug",
        "conformance-type": "implement"
      },
      {
        "name": "ietf-yang-structure-ext",
        "revision": "2020-06-17",
        "namespace": "urn:ietf:params:xml:ns:yang:ietf-yang-structure-ext",
        "conformance-type": "import"
      }
    ],
    "module-set-id": "0"
  }
}
"""

YANG_LIB = """
{
  "ietf-yang-library:modules-state": {
    "module": [
      {
        "name": "struct",
        "revision": "2026-04-05",
        "namespace": "http://example.com/struct",
        "conformance-type": "implement"
      },
      {
        "name": "ietf-yang-structure-ext",
        "revision": "2020-06-17",
        "namespace": "urn:ietf:params:xml:ns:yang:ietf-yang-structure-ext",
        "conformance-type": "import"
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
 
def test_mod_struct(data_model):
    schema_data = data_model.schema_data
    schema = data_model.schema

    id = "/struct:st"
    route = schema_data.path2route(id)
    node = schema.get_schema_descendant(route)
    assert node.sid == 67001
    assert schema_data.all_sids[67001] is node

    name = node.get_schema_descendant([("name", "struct")])
    assert name.sid == 67006
    assert schema_data.all_sids[67006] is name
    pair = node.get_schema_descendant([("pair", "struct")])
    assert pair.sid == 67007
    assert schema_data.all_sids[67007] is pair
    assert pair.children_by_sid == {
            67008: pair.get_schema_descendant([("x", "struct")]),
            67009: pair.get_schema_descendant([("y", "struct")]),
            }
    ip = node.get_schema_descendant([("ip", "struct")])
    assert ip.sid == 67002
    assert schema_data.all_sids[67002] is ip
    assert ip.children_by_sid == {
            67003: ip.get_schema_descendant([("interface", "struct")]),
            67004: ip.get_schema_descendant([("ip", "struct")]),
            67005: ip.get_schema_descendant([("packet-count", "struct")]),
            }
    values = node.get_schema_descendant([("values", "struct")])
    assert values.sid == 67010
    assert schema_data.all_sids[67010] is values

    assert node.children_by_sid == {
            67002: ip,
            67006: name,
            67007: pair,
            67010: values,
            }

@pytest.fixture
def data_model_rfc_example():
    model = yang_sid.DataModel(YANG_LIB_RFC_EXAMPLE, mod_path=MOD_PATH)
    model.set_sid_path([SID_PATH])
    model.load_all_module_sids()
    return model

def test_rfc_example(data_model_rfc_example):
    schema_data = data_model_rfc_example.schema_data
    schema = data_model_rfc_example.schema

    id = "/example-module:address-book"
    route = schema_data.path2route(id)
    node = schema.get_schema_descendant(route)
    assert node.sid == 65001
    assert schema_data.all_sids[65001] is node
    assert node.children_by_sid == {
            65002: node.get_schema_descendant([("address", "example-module")])
            }

    id = "/example-module:address-book/address"
    route = schema_data.path2route(id)
    node = schema.get_schema_descendant(route)
    assert node.sid ==  65002
    assert schema_data.all_sids[65002] is node

    last = node.get_schema_descendant([("last", "example-module")]) 
    assert last.sid == 65005
    assert schema_data.all_sids[65005] is last
    first = node.get_schema_descendant([("first", "example-module")]) 
    assert first.sid == 65004
    assert schema_data.all_sids[65004] is first
    city = node.get_schema_descendant([("city", "example-module")]) 
    assert city.sid == 65003
    assert schema_data.all_sids[65003] is city
    street = node.get_schema_descendant([("street", "example-module")]) 
    assert street.sid == 65007
    assert schema_data.all_sids[65007] is street

    # augmented nodes
    county = node.get_schema_descendant([("county", "example-module-aug")]) 
    assert county.sid == 66001
    assert schema_data.all_sids[66001] is county
    zipcode = node.get_schema_descendant([("zipcode", "example-module-aug")]) 
    assert zipcode.sid == 66002
    assert schema_data.all_sids[66002] is zipcode

    assert node.children_by_sid == {
            65003: city,
            65004: first,
            65005: last,
            65006: node.get_schema_descendant([("state", "example-module")]),
            65007: street,
            66001: county,
            66002: zipcode,
            }

