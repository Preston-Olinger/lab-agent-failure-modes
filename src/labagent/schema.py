from typing import Annotated, Literal, Union
from pydantic import BaseModel, Field

Zone = Literal["pre_pcr", "post_pcr", "thermocycler"]


class Liquid(BaseModel):
    name: str
    role: Literal["master_mix", "template", "other"] = "other"
    viscous: bool = False


class Transfer(BaseModel):
    op: Literal["transfer"]
    liquid: str
    volume_ul: float
    source: str
    dest: str
    tip: Literal["new_per_sample", "reuse"] = "new_per_sample"
    aspirate_rate_ul_s: float = 716.0
    delay_s: float = 0.0
    blow_out: bool = False


class MovePlate(BaseModel):
    op: Literal["move_plate"]
    plate: str
    from_zone: Zone
    to_zone: Zone
    fill_fraction: float = 0.0
    sealed: bool = False
    speed: Literal["default", "slow"] = "default"


Step = Annotated[Union[Transfer, MovePlate], Field(discriminator="op")]


class Protocol(BaseModel):
    liquids: dict[str, Liquid]
    steps: list[Step]
