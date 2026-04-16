import pytest
import yang_sid

from pathlib import Path

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
 
def test_mod_b(data_model):
    schema_data = data_model.schema_data
    schema = data_model.schema

    id = "/b:compound"
    route = schema_data.path2route(id)
    node = schema.get_schema_descendant(route)
    assert node.sid == 62004
    assert schema_data.all_sids[62004] is node

    id = "/b:compound/value"
    route = schema_data.path2route(id)
    node = schema.get_schema_descendant(route)
    assert node.sid == 62006
    assert schema_data.all_sids[62006] is node

def test_mod_a(data_model):
    schema_data = data_model.schema_data
    schema = data_model.schema

    # container (config=true)
    id = "/a:box/ips"
    route = schema_data.path2route(id)
    node = schema.get_schema_descendant(route)
    assert node.sid == 61015
    assert schema_data.all_sids[61015] is node

    assert node.children_by_sid == {
            61021: node.get_schema_descendant([("ips", "a")]),
            61016: node.get_schema_descendant([("add", "a")]),
            }

    # list (config=true)
    id = "/a:box/ips/ips"
    route = schema_data.path2route(id)
    node = schema.get_schema_descendant(route)
    assert node.sid == 61021
    assert schema_data.all_sids[61021] is node

    assert node.children_by_sid == {
            61022: node.get_schema_descendant([("interface", "a")]),
            61023: node.get_schema_descendant([("ip", "a")]),
            61024: node.get_schema_descendant([("packet-count", "a")]),
            61025: node.get_schema_descendant([("remove", "a")]),
            }

    # leaf (config=true)
    id = "/a:box/ips/ips/interface"
    route = schema_data.path2route(id)
    node = schema.get_schema_descendant(route)
    assert node.sid == 61022
    assert schema_data.all_sids[61022] is node

    # leaf-list (config=true)
    id = "/a:box/measurements"
    route = schema_data.path2route(id)
    node = schema.get_schema_descendant(route)
    assert node.sid == 61030
    assert schema_data.all_sids[61030] is node

    # container (config=false)
    id = "/a:misc"
    route = schema_data.path2route(id)
    node = schema.get_schema_descendant(route)
    assert node.sid == 61050
    assert schema_data.all_sids[61050] is node

    assert node.children_by_sid == {
            61051: node.get_schema_descendant([("names", "a")]),
            61052: node.get_schema_descendant([("runtime_pairs", "a")]),
            61055: node.get_schema_descendant([("simple-leaf", "a")]),
            }

    # list (config=false)
    id = "/a:misc/runtime_pairs"
    route = schema_data.path2route(id)
    node = schema.get_schema_descendant(route)
    assert node.sid == 61052
    assert schema_data.all_sids[61052] is node

    assert node.children_by_sid == {
            61053: node.get_schema_descendant([("x", "a")]),
            61054: node.get_schema_descendant([("y", "a")]),
            }

    # leaf (config=false)
    id = "/a:misc/simple-leaf"
    route = schema_data.path2route(id)
    node = schema.get_schema_descendant(route)
    assert node.sid == 61055
    assert schema_data.all_sids[61055] is node

    # leaf-list (config=false)
    id = "/a:misc/names"
    route = schema_data.path2route(id)
    node = schema.get_schema_descendant(route)
    assert node.sid == 61051
    assert schema_data.all_sids[61051] is node


def test_mod_a_sub(data_model):
    schema_data = data_model.schema_data
    schema = data_model.schema

    # submodule
    id = "/a:a-sub-data"
    route = schema_data.path2route(id)
    node = schema.get_schema_descendant(route)
    assert node.sid == 61011
    assert schema_data.all_sids[61011] is node

    # submodule augment
    # TODO: XXX: Beware that the pyang is unable to generate SID for this augmentation
    # we need to add it into the file by hand
    #id = "/b:compound/a:additional"
    #route = schema_data.path2route(id)
    #node = schema.get_schema_descendant(route)
    #assert node.sid == 61063
    #assert schema_data.all_sids[61063] is node

# no identities in ietf-inet-types and ietf-yang-types (as of rev 2025-12-22)

