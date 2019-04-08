from escape_room_core import EscapeRoom
from escape_room_packets import RequestAdmission, ProofOfPayment, PaymentResult
from escape_room_packets import RequestGame, GameRequest, GameResponse

import asyncio, os, pickle

from playground.common.CipherUtil import loadCertFromFile, RSA_SIGNATURE_MAC
from BankCore import LedgerLineStorage, LedgerLine
from OnlineBankConfig import OnlineBankConfig

import playground
from playground.network.packet import PacketType


class PaymentProcessing:
    def __init__(self):
        self._bankconfig = OnlineBankConfig()
        
        # TODO: This is hard coded. It needs to be changed to be part of the ini
        certPath = os.path.join(self._bankconfig.path(), "bank.cert")
        
        
        self._cert = loadCertFromFile(certPath)
        self._account = None
        self._price   = None
        self._total   = 0
        self._tokens  = {}
        
    def configure(self, account, price):
        self._account = account
        self._price   = price
        
    def createAdmissionRequest(self):
        if self._account == None or self._price == None:
            raise Exception("Not properly configured.")
        token = int.from_bytes(os.urandom(4), byteorder="big")
        req_admission = RequestAdmission(
            account=self._account,
            amount =self._price,
            token  =token
        )
        self._tokens[ token ] = "WAITING"
        return req_admission
        
    def _verifyReceiptSignature(self, receipt, signature):
        verifier = RSA_SIGNATURE_MAC(self._cert.public_key())
        return verifier.verify(receipt, signature)
        
    def _verifyReceipt(self, receipt, expected_token):
        ledger_line = LedgerLineStorage.deserialize(receipt)
        memo = ledger_line.memo(self._account)
        if str(memo) != str(expected_token):
            return "Mismatching token in memo (expected {} got {})".format(
                expected_token,
                memo)
        amount = ledger_line.getTransactionAmount(self._account)
        if amount != self._price:
            return "Mismatching amount (expected {} got {})".format(
                self._price,
                amount)
        return "Verified"
        
        
    def process(self, token, receipt, signature):
        if token in self._tokens:
            del self._tokens[token]
            if not self._verifyReceiptSignature(receipt, signature):
                return "Signature failed"
            return self._verifyReceipt(receipt, token)
        return "Unknown Token"
global_payment_processor = PaymentProcessing()

class EscapeRoomServerProtocol(asyncio.Protocol):
    def __init__(self):
        self._buffer = PacketType.Deserializer()
        
    def connection_made(self, transport):
        print("Server connected")
        self.transport = transport
        
    def data_received(self, data):
        self._buffer.update(data)
        for packet in self._buffer.nextPackets():
            if isinstance(packet, RequestGame):
                req = global_payment_processor.createAdmissionRequest()
                self.transport.write(req.__serialize__())
            elif isinstance(packet, ProofOfPayment):
                payment_status = global_payment_processor.process(
                    packet.token,
                    packet.receipt, 
                    packet.signature)
                if payment_status == "Verified":
                    self._token = packet.token
                    
                    self._escape_room = EscapeRoom()
                    self._escape_room.start()
                    response = PaymentResult(
                        token=   self._token,
                        accepted=True,
                        message= payment_status)
                    self.transport.write(response.__serialize__())
                else:
                    response = PaymentResult(
                        token=   packet.token,
                        accepted=False,
                        message= payment_status)
                    self.transport.write(response.__serialize__())
                    self.transport.close()
            elif isinstance(packet, GameRequest):
                if packet.token != self._token:
                    self.transport.close()
                else:
                    response = self._escape_room.command(packet.command)
                    status   = self._escape_room.status()
                    game_response = GameResponse(
                        response=response,
                        status  =status)
                    self.transport.write(game_response.__serialize__())
                    if status != "locked":
                        self.transport.close()
                    
if __name__=="__main__":
    import sys, argparse
    #from playground.common.logging import EnablePresetLogging, PRESET_DEBUG
    #EnablePresetLogging(PRESET_DEBUG)
    
    parser = argparse.ArgumentParser()
    parser.add_argument("account")
    parser.add_argument("-p", "--port", default=5678)
    parser.add_argument("--price", default=5)
    
    args = parser.parse_args(sys.argv[1:])
    global_payment_processor.configure(args.account, int(args.price))
    
    loop = asyncio.get_event_loop()
    coro = playground.create_server(EscapeRoomServerProtocol, host='localhost', port=args.port)
    server = loop.run_until_complete(coro)
    
    # Serve requests until Ctrl+C is pressed
    print('Serving on {}'.format(server.sockets[0].getsockname()))
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass

    # Close the server
    server.close()
    loop.run_until_complete(server.wait_closed())
    loop.close()