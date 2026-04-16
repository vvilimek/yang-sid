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
        "name": "ietf-restconf",
        "revision": "2017-01-26",
        "namespace": "urn:ietf:params:xml:ns:yang:ietf-restconf",
        "conformance-type": "implement"
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
        "name": "yd",
        "revision": "2026-04-04",
        "namespace": "http://example.com/yangdata",
        "conformance-type": "implement"
      },
      {
        "name": "ietf-restconf",
        "revision": "2017-01-26",
        "namespace": "urn:ietf:params:xml:ns:yang:ietf-restconf",
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
 
def test_mod_yd(data_model):
    schema_data = data_model.schema_data
    schema = data_model.schema

    id = "/yd:yd-box"
    route = schema_data.path2route(id)
    node = schema.get_schema_descendant(route)
    assert node.sid == 69001
    assert schema_data.all_sids[69001] is node

    version = node.get_schema_descendant([("version", "yd")])
    assert version.sid == 69010
    assert schema_data.all_sids[69010] is version
    mgmt = node.get_schema_descendant([("mgmt", "yd")])
    assert mgmt.sid == 69006
    assert schema_data.all_sids[69006] is mgmt
    assert mgmt.children_by_sid == {
            69008: mgmt.get_schema_descendant([("user", "yd")]),
            69007: mgmt.get_schema_descendant([("access-rights", "yd")]),
            }
    ip = node.get_schema_descendant([("ip", "yd")])
    assert ip.sid == 69002
    assert schema_data.all_sids[69002] is ip
    assert ip.children_by_sid == {
            69003: ip.get_schema_descendant([("interface", "yd")]),
            69004: ip.get_schema_descendant([("ip", "yd")]),
            69005: ip.get_schema_descendant([("packet-count", "yd")]),
            }
    peers = node.get_schema_descendant([("peers", "yd")])
    assert peers.sid == 69009
    assert schema_data.all_sids[69009] is peers

    assert node.children_by_sid == {
            69002: ip,
            69006: mgmt,
            69009: peers,
            69010: version,
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

    id = "/ietf-restconf:errors"
    route = schema_data.path2route(id)
    node = schema.get_schema_descendant(route)
    assert node.sid == 68001
    assert schema_data.all_sids[68001] is node

    error = node.get_schema_descendant([("error", "ietf-restconf")])
    assert error.sid == 68002
    assert schema_data.all_sids[68002] is error

    assert node.children_by_sid == {68002: error}

    app_tag = error.get_schema_descendant([("error-app-tag", "ietf-restconf")]) 
    assert app_tag.sid == 68003
    assert schema_data.all_sids[68003] is app_tag
    info = error.get_schema_descendant([("error-info", "ietf-restconf")]) 
    assert info.sid == 68004
    assert schema_data.all_sids[68004] is info
    message = error.get_schema_descendant([("error-message", "ietf-restconf")]) 
    assert message.sid == 68005
    assert schema_data.all_sids[68005] is message
    path = error.get_schema_descendant([("error-path", "ietf-restconf")]) 
    assert path.sid == 68006
    assert schema_data.all_sids[68006] is path
    tag = error.get_schema_descendant([("error-tag", "ietf-restconf")]) 
    assert tag.sid == 68007
    assert schema_data.all_sids[68007] is tag
    err_type = error.get_schema_descendant([("error-type", "ietf-restconf")]) 
    assert err_type.sid == 68008
    assert schema_data.all_sids[68008] is err_type

    assert error.children_by_sid == {
            68003: app_tag,
            68004: info,
            68005: message,
            68006: path,
            68007: tag,
            68008: err_type,
            }

