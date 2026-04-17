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
        "feature": ["a-feature-ident"],
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
def schema_data():
    model = yang_sid.DataModel(YANG_LIB, mod_path=MOD_PATH)
    model.set_sid_path([SID_PATH])
    model.load_all_sid_files()
    return model.schema_data

def test_mod_c(schema_data):
    # import modules do not contribute with identities
    assert ("c-identity", "c") not in schema_data.identity_adjs
    assert 63001 not in schema_data.all_sids
    
def test_mod_b(schema_data):
    assert schema_data.sid_identities[("b-base", "b")] == 62001
    assert schema_data.identities_by_sid[62001] == ("b-base", "b")
    assert schema_data.all_sids[62001] == ("b-base", "b")

    assert schema_data.sid_identities[("b-derived", "b")] == 62002
    assert schema_data.identities_by_sid[62002] == ("b-derived", "b")
    assert schema_data.all_sids[62002] == ("b-derived", "b")

def test_mod_a(schema_data):
    assert schema_data.sid_identities[("a-base", "a")] == 61002
    assert schema_data.identities_by_sid[61002] == ("a-base", "a")
    assert schema_data.all_sids[61002] == ("a-base", "a")

    # identity with if-feature
    assert schema_data.sid_identities[("a-conditional", "a")] == 61003
    assert schema_data.identities_by_sid[61003] == ("a-conditional", "a")
    assert schema_data.all_sids[61003] == ("a-conditional", "a")

    assert schema_data.sid_identities[("a-simple", "a")] == 61004
    assert schema_data.identities_by_sid[61004] == ("a-simple", "a")
    assert schema_data.all_sids[61004] == ("a-simple", "a")

    assert schema_data.sid_identities[("complex", "a")] == 61005
    assert schema_data.identities_by_sid[61005] == ("complex", "a")
    assert schema_data.all_sids[61005] == ("complex", "a")


# no identities in ietf-inet-types and ietf-yang-types (as of rev 2025-12-22)

