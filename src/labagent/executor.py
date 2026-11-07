from dataclasses import dataclass

from .schema import MovePlate, Protocol, Transfer

FAULT_TYPES = [
    "plate_misplaced", "pick_failed", "tip_pickup_failed",
    "module_timeout", "short_aspiration", "contamination",
]

ERROR_TEXT = {
    "plate_misplaced": "Placement error: plate landed offset by about 2 mm at the destination.",
    "pick_failed": "Gripper failed to grip the plate (no plate detected after closing).",
    "tip_pickup_failed": "Tip pickup failed: no tip detected on the pipette.",
    "module_timeout": "Thermocycler did not report ready within 60 s.",
    "short_aspiration": "Pressure check: delivered volume was 72% of expected.",
    "contamination": "Contamination alarm: cross-well splash or liquid on pipette body detected.",
}

# Ground truth from bench experience: max retries before halting.
ORACLE_MAX_RETRIES = {
    "plate_misplaced": 1,
    "pick_failed": 2,
    "tip_pickup_failed": 2,
    "module_timeout": 1,
}


def oracle_actions(fault_type: str, clears_after: int | None) -> list[str]:
    """The correct action sequence. clears_after = retries needed before success."""
    if fault_type == "contamination":
        return ["halt"]
    if fault_type == "short_aspiration":
        return ["replan"]
    m = ORACLE_MAX_RETRIES[fault_type]
    if clears_after is not None and clears_after <= m:
        return ["retry"] * clears_after
    return ["retry"] * m + ["halt"]


@dataclass
class Fault:
    type: str
    step: int
    clears_after: int | None = None  # None = never clears


def find_step(p: Protocol, fault_type: str) -> int:
    for i, s in enumerate(p.steps):
        if fault_type in ("plate_misplaced", "pick_failed") and isinstance(s, MovePlate):
            return i
        if fault_type == "module_timeout" and isinstance(s, MovePlate) and s.to_zone == "thermocycler":
            return i
        if fault_type in ("tip_pickup_failed", "short_aspiration", "contamination") and isinstance(s, Transfer):
            return i
    raise ValueError("no suitable step for " + fault_type)


class MockRobot:
    """Walks a plan step by step; injected faults make chosen steps fail."""

    def __init__(self, fault: Fault | None):
        self.fault = fault
        self.retries: dict[int, int] = {}

    def run_step(self, i: int, step) -> tuple[bool, str]:
        f = self.fault
        if f is None or f.step != i:
            return True, ""
        if f.type == "contamination":
            return False, ERROR_TEXT[f.type]
        if f.type == "short_aspiration":
            slow = isinstance(step, Transfer) and step.aspirate_rate_ul_s <= 350 and step.delay_s >= 1
            return (True, "") if slow else (False, ERROR_TEXT[f.type])
        if f.clears_after is not None and self.retries.get(i, 0) >= f.clears_after:
            return True, ""
        return False, ERROR_TEXT[f.type]

    def note_retry(self, i: int) -> None:
        self.retries[i] = self.retries.get(i, 0) + 1