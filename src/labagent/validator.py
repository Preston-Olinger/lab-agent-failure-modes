from dataclasses import dataclass

from .schema import MovePlate, Protocol, Transfer

# Tunable heuristics from bench experience, NOT simulated physics.
MAX_VISCOUS_RATE_UL_S = 350.0
MIN_VISCOUS_DELAY_S = 1.0
MAX_FILL_UNSEALED = 0.8


@dataclass
class Violation:
    rule: str
    step: int | None
    message: str


def validate(p: Protocol) -> list[Violation]:
    v: list[Violation] = []
    mm_first: dict[str, int] = {}
    tmpl_first: dict[str, int] = {}
    prev_source: str | None = None
    if not p.steps:
        v.append(Violation("R9", None, "plan has no steps"))

    for i, s in enumerate(p.steps):
        if isinstance(s, Transfer):
            liq = p.liquids.get(s.liquid)
            if liq is None:
                v.append(Violation("R0", i, f"unknown liquid '{s.liquid}'"))
                continue
            if liq.viscous and (
                s.aspirate_rate_ul_s > MAX_VISCOUS_RATE_UL_S
                or s.delay_s < MIN_VISCOUS_DELAY_S
                or not s.blow_out
            ):
                v.append(Violation("R2", i, "viscous liquid needs slow rate, delay, and blow-out"))
            if s.tip == "reuse" and (
                liq.role == "template"
                or (prev_source is not None and prev_source != s.source)
            ):
                v.append(Violation("R3", i, "tip reused across different samples"))
            prev_source = s.source
            if liq.role == "master_mix":
                mm_first.setdefault(s.dest, i)
            if liq.role == "template":
                tmpl_first.setdefault(s.dest, i)
        elif isinstance(s, MovePlate):
            if s.from_zone == "post_pcr" and s.to_zone == "pre_pcr":
                v.append(Violation("R6", i, "post-PCR plate moved back to pre-PCR area"))
            if s.fill_fraction > MAX_FILL_UNSEALED and not (s.sealed or s.speed == "slow"):
                v.append(Violation("R7", i, "high-fill plate moved unsealed at default speed"))
            if s.to_zone == "thermocycler" and not s.sealed:
                v.append(Violation("R8", i, "unsealed plate sent to thermocycler"))

    for well, t_idx in tmpl_first.items():
        if well in mm_first and mm_first[well] > t_idx:
            v.append(Violation("R4", t_idx, f"template added before master mix in {well}"))

    if mm_first and not [w for w in mm_first if w not in tmpl_first]:
        v.append(Violation("R5", None, "no no-template control well"))

    return v
