import pytest

import yang_sid
from yang_sid.__main__ import main

import subprocess
from pathlib import Path

def get_root_dir():
    ys_dir = Path(yang_sid.__file__).parent
    return ys_dir.parent.parent

@pytest.fixture
def root_dir():
    return get_root_dir()

def test_sid_costs(capsys, root_dir):
    with open(root_dir / "tests" / "costs.out", mode="r", encoding="utf8") as file:
        expected_output = file.read()

    with capsys.disabled():
        proc = subprocess.run(["uv", "run", "yang-sid", 
                       "-t", 
                       "--sid", 
                       "--sid-cost", 
                       "-p", f"{root_dir / 'yang_modules'}:{root_dir / 'src' / 'yang_sid' / 'yang_modules'}", 
                       "--sid-path", root_dir / "sid", 
                       root_dir / "lib" / "costs-lib.json"],
                capture_output=True)

    assert proc.stdout.decode(encoding="utf8") == expected_output


LIBRARIES = (get_root_dir() / "lib" / "system-lib.json",
             get_root_dir() / "lib" / "struct-lib.json",
             get_root_dir() / "lib" / "rpc-action.json",
             get_root_dir() / "lib" / "yd-lib.json",)

@pytest.mark.parametrize("lib_file", LIBRARIES)
def test_lib(root_dir, lib_file):
    # this test checks that no exception is being raised
    main(infile=lib_file,
         tree=True,
         sid=True,
         sid_cost=True,
         path=f"{root_dir / 'yang_modules'}:{root_dir / 'src' / 'yang_sid' / 'yang_modules'}",
         sid_path=str(root_dir / "sid")
         )

