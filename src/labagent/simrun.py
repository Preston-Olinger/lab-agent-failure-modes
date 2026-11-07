import pathlib
import subprocess
import sys
import tempfile
from dataclasses import dataclass


@dataclass
class SimResult:
    ok: bool
    output: str


def run_simulation(code: str) -> SimResult:
    with tempfile.TemporaryDirectory() as d:
        f = pathlib.Path(d) / "protocol.py"
        f.write_text(code)
        r = subprocess.run(
            [sys.executable, "-c",
             "import sys; from opentrons.simulate import main; sys.exit(main())",
             str(f)],
            capture_output=True, text=True,
        )
    out = (r.stdout + r.stderr).strip()
    return SimResult(ok=(r.returncode == 0 and "Error" not in out), output=out)
