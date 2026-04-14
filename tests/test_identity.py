import pytest
import yang_sid

from pathlib import Path

SID_DIR = Path(yang_sid.__file__).parent.parent.parent / "sid"

yang_lib = """
{
  "ietf-yang-library:modules-state": {
    "module-set": [
      {
	"name": "a",
	"revision": "2026-04-03",
	"namespace": "http://example.com/a/main",
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
    model = yang_sid.DataModel(yang_lib)
    model.load_sid_file(SID_DIR / "a@2026-04-03.sid")
    model.load_sid_file(SID_DIR / "b@2026-04-01.sid")
    model.load_sid_file(SID_DIR / "c@2025-04-02.sid")
    return model.schema_data

def test_mod_c(schema_data):
    mod_data = schema_data.module_by_sid[63000]

    assert mod_data.name == "c" and mod_data.revision == "2026-04-02"
    assert schema_data.all_sids[63000] is mod_data
    assert mod_data.sid == 63000
    
def test_mod_b(schema_data):
    mod_data = schema_data.module_by_sid[62000]

    assert mod_data.name == "b" and mod_data_revision == "2026-04-01"
    assert schema_data.all_sids[62000] is mod_data
    assert mod_data.sid == 62000

def test_mod_a(schema_data):
    mod_data = schema_data.module_by_sid[61000]

    assert mod_data.name == "a" and mod_data.revision == "2026-04-03"
    assert schema_data.all_sids[61000] is mod_data
    assert mod_data.sid == 61000

    assert len(mod_data.submodules) == 1
    for submod in mod_data.submodules:
        submod_data = schema_data.modules[submod]
        assert submod_data.name == "a-sub" and submod_data.revisin == "2026-04-03"
        assert schema_data.all_sids[61001] is submod_data
        assert submod_data.sid == 61001

def testi_ietf_mods(schema_data):
    yang = schema_data.module_by_name["ietf-yang-types"]
    inet = schema_data.module_by_name["ietf-inet-types"]

    assert yang.sid == 1100
    assert inet.sid == 1150

