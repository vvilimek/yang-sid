import yang_sid

import subprocess
from pathlib import Path

def test_sid_prices(capsys):
    ys_dir = Path(yang_sid.__file__).parent
    root_dir = ys_dir.parent.parent

    with open(root_dir / "tests" / "prices.out", mode="r", encoding="utf8") as file:
        expected_output = file.read()

    with capsys.disabled():
        proc = subprocess.run(["uv", "run", "yang-sid", 
                       "-t", 
                       "--sid", 
                       "--sid-price", 
                       "-p", f"{root_dir / 'yang_modules'}:{root_dir / 'src' / 'yang_sid' / 'yang_modules'}", 
                       "--sid-path", root_dir / "sid", 
                       root_dir / "lib" / "prices-lib.json"],
                capture_output=True)

    assert proc.stdout.decode(encoding="utf8") == expected_output



