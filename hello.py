from opentrons import protocol_api

metadata = {"protocolName": "hello"}
requirements = {"robotType": "Flex", "apiLevel": "2.19"}

def run(protocol: protocol_api.ProtocolContext):
    trash = protocol.load_trash_bin("A3")
    plate = protocol.load_labware("corning_96_wellplate_360ul_flat", "D1")
    tips = protocol.load_labware("opentrons_flex_96_tiprack_200ul", "D2")
    p1000 = protocol.load_instrument("flex_1channel_1000", "left", tip_racks=[tips])
    p1000.pick_up_tip()
    p1000.aspirate(50, plate["A1"])
    p1000.dispense(50, plate["B1"])
    p1000.drop_tip()
