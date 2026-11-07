import json
from typing import TypedDict

import anthropic
from dotenv import load_dotenv
from langgraph.graph import END, START, StateGraph

from .executor import Fault, MockRobot
from .schema import Protocol

load_dotenv()
client = anthropic.Anthropic()
MODEL = "claude-haiku-5-5"

DECIDE_PROMPT = """A step failed during an automated PCR liquid-handling run on a robot.
Step: {step}
Error: {error}
Retries already attempted on this step: {retries}
Actions taken so far in this run: {actions}
Choose exactly one action:
- retry: run the same step again
- replan: change the step to use slower aspiration, a delay, and a blow-out, then run it again
- halt: stop the run and ask a human
Reply with ONLY JSON: {{"action": "retry|replan|halt", "reason": "one sentence"}}"""


class RunState(TypedDict, total=False):
    protocol: dict
    robot: object
    strategy: str
    i: int
    retries: int
    actions: list
    reasons: list
    status: str
    last_error: str
    next_action: str


def execute(state: RunState) -> dict:
    p = Protocol.model_validate(state["protocol"])
    i = state["i"]
    if i >= len(p.steps):
        return {"status": "completed"}
    ok, err = state["robot"].run_step(i, p.steps[i])
    if ok:
        return {"i": i + 1, "retries": 0, "status": "running", "last_error": ""}
    return {"status": "faulted", "last_error": err}


def decide(state: RunState) -> dict:
    s = state["strategy"]
    reason = ""
    if s == "A":
        action = "halt"
    elif s == "B":
        action = "retry" if state["retries"] < 3 else "halt"
    else:
        step = state["protocol"]["steps"][state["i"]]
        msg = DECIDE_PROMPT.format(step=json.dumps(step), error=state["last_error"],
                                   retries=state["retries"], actions=state["actions"])
        r = client.messages.create(model=MODEL, max_tokens=1000,
                                   messages=[{"role": "user", "content": msg}])
        text = "".join(b.text for b in r.content if b.type == "text").strip()
        if text.startswith("```"):
            text = text.strip("`").removeprefix("json").strip()
        try:
            d = json.loads(text)
            action = d["action"]
            reason = str(d.get("reason", ""))
        except Exception:
            action, reason = "halt", "unparseable decision"
        if action not in ("retry", "replan", "halt"):
            action, reason = "halt", "invalid action"
    return {"next_action": action, "reasons": state["reasons"] + [reason]}


def apply(state: RunState) -> dict:
    a = state["next_action"]
    i = state["i"]
    if a != "halt" and len(state["actions"]) >= 5:
        a = "halt"  # safety cap against endless loops
    acts = state["actions"] + [a]
    if a == "halt":
        return {"actions": acts, "status": "halted"}
    if a == "retry":
        state["robot"].note_retry(i)
        return {"actions": acts, "retries": state["retries"] + 1}
    steps = [dict(x) for x in state["protocol"]["steps"]]
    steps[i].update(aspirate_rate_ul_s=300.0, delay_s=1.0, blow_out=True)
    return {"actions": acts, "retries": state["retries"] + 1,
            "protocol": {**state["protocol"], "steps": steps}}


def after_execute(state: RunState) -> str:
    if state["status"] == "completed":
        return "done"
    if state["status"] == "faulted":
        return "decide"
    return "execute"


def after_apply(state: RunState) -> str:
    return "done" if state["status"] == "halted" else "execute"


g = StateGraph(RunState)
g.add_node("execute", execute)
g.add_node("decide", decide)
g.add_node("apply", apply)
g.add_edge(START, "execute")
g.add_conditional_edges("execute", after_execute,
                        {"done": END, "decide": "decide", "execute": "execute"})
g.add_edge("decide", "apply")
g.add_conditional_edges("apply", after_apply, {"done": END, "execute": "execute"})
graph = g.compile()


def run_scenario(p: Protocol, fault: Fault | None, strategy: str) -> dict:
    return graph.invoke(
        {"protocol": p.model_dump(), "robot": MockRobot(fault), "strategy": strategy,
         "i": 0, "retries": 0, "actions": [], "reasons": [], "status": "running",
         "last_error": ""},
        {"recursion_limit": 60},
    )