from playground.network.packet import PacketType
from playground.network.packet.fieldtypes import BOOL, STRING, UINT16, UINT32, BUFFER

class RequestGame(PacketType):
    DEFINITION_IDENTIFIER = "samples.escape_room_for_profit.RequestGame"
    DEFINITION_VERSION = "1.0"
    FIELDS = []

class RequestAdmission(PacketType):
    DEFINITION_IDENTIFIER = "samples.escape_room_for_profit.RequestAdmission"
    DEFINITION_VERSION = "1.0"
    FIELDS = [
        ("account", STRING),
        ("amount",  UINT16),
        ("token",   UINT32)
    ]
    
class ProofOfPayment(PacketType):
    DEFINITION_IDENTIFIER = "samples.escape_room_for_profit.ProofOfPayment"
    DEFINITION_VERSION = "1.0"
    FIELDS = [
        ("token",     UINT32),
        ("receipt",   BUFFER),
        ("signature", BUFFER)
    ]
    
class PaymentResult(PacketType):
    DEFINITION_IDENTIFIER = "samples.escape_room_for_profit.PaymentResult"
    DEFINITION_VERSION = "1.0"
    FIELDS = [
        ("token",    UINT32),
        ("accepted", BOOL),
        ("message",  STRING)
        ]
    
class GameRequest(PacketType):
    DEFINITION_IDENTIFIER = "samples.escape_room_for_profit.GameRequest"
    DEFINITION_VERSION = "1.0"
    FIELDS = [
        ("token",   UINT32),
        ("command", STRING)
    ]
    
class GameResponse(PacketType):
    DEFINITION_IDENTIFIER = "samples.escape_room_for_profit.GameResponse"
    DEFINITION_VERSION = "1.0"
    FIELDS = [
        ("response", STRING),
        ("status",   STRING)
    ]