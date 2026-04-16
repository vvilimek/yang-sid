import yang_sid
import pytest

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
 
def test_mod_a_notification(data_model):
    schema_data = data_model.schema_data
    schema = data_model.schema

    id = "/a:something-changed"
    route = schema_data.path2route(id)
    node = schema.get_schema_descendant(route)
    assert node.sid == 61063
    assert schema_data.all_sids[61063] is node
    time = node.get_schema_descendant([("time", "a")])
    assert time.sid == 61065
    assert schema_data.all_sids[61065] is time
    what = node.get_schema_descendant([("what", "a")])
    assert what.sid == 61066
    assert schema_data.all_sids[61066] is what
    new_value_str = node.get_schema_descendant([("new-value-str", "a")])
    assert new_value_str.sid == 61064
    assert schema_data.all_sids[61064] is new_value_str

    assert node.children_by_sid == {
            61064: new_value_str,
            61065: time,
            61066: what,
            }


 
# no notifications in ietf-yang-types, ietf-inet-types

