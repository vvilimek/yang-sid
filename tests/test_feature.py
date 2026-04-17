# SPDX-FileCopyrightText: CZ.NIC z.s.p.o.
#
# SPDX-License-Identifier: LGPL-3.0-or-later

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
        "feature": ["a-feature", "a-feature-tree", "a-feature-ident", "a-feature-test", "a-sub-feature"],
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
        "feature": ["c-feature-impl"],
        "conformance-type": "import"
      },
      {
        "name": "ietf-inet-types",
        "revision": "2025-12-22",
        "namespace": "urn:ietf:params:xml:ns:yang:ietf-inet-types",
        "conformance-type": "import"
      },
      {
        "name": "ietf-yang-types",
        "revision": "2025-12-22",
        "namespace": "urn:ietf:params:xml:ns:yang:ietf-yang-types",
        "conformance-type": "import"
      }
    ],
    "module-set-id": "0"
  }
}
"""

@pytest.fixture
def schema_data():
    model = yang_sid.DataModel(YANG_LIB, mod_path=MOD_PATH)
    model.set_sid_path([SID_PATH])
    schema_data = model.schema_data
    model.load_module_sids(schema_data.modules_by_name["a"])
    model.load_module_sids(schema_data.modules_by_name["b"])
    model.load_module_sids(schema_data.modules_by_name["c"])
    model.load_module_sids(schema_data.modules_by_name["ietf-inet-types"])
    model.load_module_sids(schema_data.modules_by_name["ietf-yang-types"])
    return schema_data

def test_mod_c(schema_data):
    mod_data = schema_data.modules_by_sid[63000]
    assert mod_data.yang_id == ("c", "2026-04-02")
 
    # not implemented feature (of import module)
    assert "c-feature" not in mod_data.sid_features
    assert 63002 not in mod_data.features_by_sid
    assert "c-feature" not in mod_data.features
    assert 63002 not in schema_data.all_sids

    # implemented feature (of import module)
    assert mod_data.sid_features["c-feature-impl"] == 63003
    assert mod_data.features_by_sid[63003] == "c-feature-impl"
    assert "c-feature-impl" in mod_data.features
    assert schema_data.all_sids[63003] == "c-feature-impl"
 
def test_mod_b(schema_data):
    mod_data = schema_data.modules_by_sid[62000]
    assert mod_data.yang_id == ("b", "2026-04-01")

    # not implemented feature (of implement module)
    assert "b-feature" not in mod_data.sid_features
    assert 62003 not in mod_data.features_by_sid
    assert "b-feature" not in mod_data.features
    assert 62003 not in schema_data.all_sids

def test_mod_a(schema_data):
    mod_data = schema_data.modules_by_sid[61000]
    assert mod_data.yang_id == ("a", "2026-04-03")

    # implemented
    for (feat_name, feat_sid) in [("a-feature", 61006), ("a-feature-ident", 61007), ("a-feature-test", 61008), 
                                  ("a-feature-tree", 61009)]:
        assert mod_data.sid_features[feat_name] == feat_sid
        assert mod_data.features_by_sid[feat_sid] == feat_name
        assert feat_name in mod_data.features
        assert schema_data.all_sids[feat_sid] == feat_name


    # submodule features are registered at main module ModuleData
    (feat_name, feat_sid) = ("a-sub-feature", 61010)
    assert mod_data.sid_features[feat_name] == feat_sid
    assert mod_data.features_by_sid[feat_sid] == feat_name
    assert feat_name in mod_data.features
    assert schema_data.all_sids[feat_sid] == feat_name

