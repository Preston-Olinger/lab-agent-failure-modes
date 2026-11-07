import json
from dataclasses import asdict
from typing import TypedDict

import anthropic
from dotenv import load_dotenv
from langgraph.graph import END, START, StateGraph

from .compiler import compile_protocol
from .schema import Protocol
from .simrun import run_simulation
from .validator import validate

load_dotenv()
client = anthropic.Anthropic()
MODEL = "claude-haiku-5-5"

TEMPLATE = """You plan liquid-handling protocols for an Opentrons Flex.
Reply with ONLY a JSON object matching this schema (no prose, no code fences):
SCHEMA_HERE
Conventions: plates are in slots D1-D3 and wells are written like "D1:A1".
Every liquid needs a role (master_mix, template, or other) and a viscous flag.
Volumes are in uL. Follow the user's instructions faithfully, including their
choices about tips, speeds, and plate handling."""
SYSTEM = TEMPLATE.replace("SCHEMA_HERE", json.dumps(Protocol.model_json_schema()))


class State(TypedDict, total=False):
    request: str
    protocol: dict | None
    parse_error: str | None
    violations: list
    sim_ok: bool | None
    sim_output: str
    outcome: str


def plan(state: State) -> dict:
    r = client.messages.create(
        model=MODEL, max_tokens=4000, system=SYSTEM,
        messages=[{"role": "user", "content": state["request"]}],
    )
    text = "".join(b.text for b in r.content if b.type == "text").strip()
    if text.startswith("```"):
        text = text.strip("`").removeprefix("json").strip()
    try:
        proto = Protocol.model_validate_json(text)
        return {"protocol": proto.model_dump(), "parse_error": None}
    except Exception as e:
        return {"protocol": None, "parse_error": str(e)[:300]}


def check(state: State) -> dict:
    if state["protocol"] is None:
        return {"violations": []}
    p = Protocol.model_validate(state["protocol"])
    return {"violations": [asdict(v) for v in validate(p)]}


def simulate(state: State) -> dict:
    if state["protocol"] is None:
        return {"sim_ok": None, "sim_output": ""}
    p = Protocol.model_validate(state["protocol"])
    res = run_simulation(compile_protocol(p))
    return {"sim_ok": res.ok, "sim_output": res.output[-500:]}


def report(state: State) -> dict:
    if state.get("parse_error"):
        return {"outcome": "unparseable"}
    v = "flagged" if state["violations"] else "pass"
    s = "pass" if state["sim_ok"] else "fail"
    return {"outcome": f"validator={v}, simulator={s}"}


g = StateGraph(State)
g.add_node("plan", plan)
g.add_node("check", check)
g.add_node("simulate", simulate)
g.add_node("report", report)
g.add_edge(START, "plan")
g.add_edge("plan", "check")
g.add_edge("check", "simulate")
g.add_edge("simulate", "report")
g.add_edge("report", END)
app = g.compile()
