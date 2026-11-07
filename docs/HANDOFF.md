# Handoff (end of Saturday)

## Done
- Q1: schema, validator (R2-R9), compiler, simulator wrapper, LangGraph plan graph; 30 requests x 3 runs (results/q1_*).
- Q2: mock robot, fault injection, recovery graph; strategies A/B/C/D (results/q2_*).
- Q6: OpenTelemetry tracing into Jaeger for the recovery graph.
- Findings and caveats are in docs/notes.md.

## To do
1. Fix retries counter (it increments on replan; the model sees "retries: 1" after only a replan) in src/labagent/exec_graph.py, then rerun experiments/run_q2.py.
2. Optional: neutral-wording rerun of Q2 (error text says "splash"; replan option describes slowing aspiration).
3. Dockerfile, then Kubernetes Job on kind (cap this at 90 minutes).
4. README with results tables and honest limitations.
5. Update resume; test a clean clone.

## Restart commands
cd ~/Documents/lab-agent-project
conda activate labagent
export PYTHONPATH=src
docker start jaeger   (UI at http://localhost:16686)

## Notes
- .env (API key) is local only and not in GitHub.
- Opentrons 10.x needs Flex protocols; Python 3.12 conda env named labagent.
