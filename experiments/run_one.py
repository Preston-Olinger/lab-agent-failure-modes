import json
import sys

from labagent.graph import app

res = app.invoke({"request": " ".join(sys.argv[1:])})
keys = ("outcome", "violations", "sim_ok", "parse_error", "protocol", "sim_output")
print(json.dumps({k: res.get(k) for k in keys}, indent=2))
