from .schema import MovePlate, Protocol, Transfer

HEADER = '''from opentrons import protocol_api

metadata = {"protocolName": "generated"}
requirements = {"robotType": "Flex", "apiLevel": "2.19"}


def run(protocol: protocol_api.ProtocolContext):
    protocol.load_trash_bin("A3")
    tips = protocol.load_labware("opentrons_flex_96_tiprack_200ul", "C1")
    pip = protocol.load_instrument("flex_1channel_1000", "left", tip_racks=[tips])
'''


def _split(loc: str) -> tuple[str, str]:
    slot, well = loc.split(":")
    return slot, well


def compile_protocol(p: Protocol) -> str:
    slots: set[str] = set()
    for s in p.steps:
        if isinstance(s, Transfer):
            slots.add(_split(s.source)[0])
            slots.add(_split(s.dest)[0])

    out = [HEADER]
    for slot in sorted(slots):
        out.append(f'    plate_{slot} = protocol.load_labware("corning_96_wellplate_360ul_flat", "{slot}")\n')

    for s in p.steps:
        if isinstance(s, Transfer):
            ss, sw = _split(s.source)
            ds, dw = _split(s.dest)
            if s.tip == "new_per_sample":
                out.append("    if pip.has_tip:\n        pip.drop_tip()\n    pip.pick_up_tip()\n")
            else:
                out.append("    if not pip.has_tip:\n        pip.pick_up_tip()\n")
            out.append(f"    pip.flow_rate.aspirate = {s.aspirate_rate_ul_s}\n")
            out.append(f"    pip.flow_rate.dispense = {s.aspirate_rate_ul_s}\n")
            out.append(f'    pip.aspirate({s.volume_ul}, plate_{ss}["{sw}"])\n')
            if s.delay_s > 0:
                out.append(f"    protocol.delay(seconds={s.delay_s})\n")
            out.append(f'    pip.dispense({s.volume_ul}, plate_{ds}["{dw}"])\n')
            if s.blow_out:
                out.append(f'    pip.blow_out(plate_{ds}["{dw}"])\n')
        elif isinstance(s, MovePlate):
            # Zones are abstract: moves are validated by rules, not executed.
            out.append(f'    protocol.comment("move_plate {s.plate}: {s.from_zone} -> {s.to_zone}")\n')

    out.append("    if pip.has_tip:\n        pip.drop_tip()\n")
    return "".join(out)
