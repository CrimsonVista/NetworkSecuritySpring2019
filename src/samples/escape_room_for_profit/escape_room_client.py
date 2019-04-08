from escape_room_packets import RequestAdmission, ProofOfPayment, PaymentResult
from escape_room_packets import RequestGame, GameRequest, GameResponse

import asyncio, sys, getpass, os, playground
from OnlineBank import BankClientProtocol
from OnlineBankConfig import OnlineBankConfig
from playground.network.packet import PacketType
from playground.common.CipherUtil import loadCertFromFile

input_queue = []
output_queue = []

class PaymentProcessing:
    def __init__(self):
        self._bankconfig = OnlineBankConfig()
        # TODO: This is hard coded. It needs to be changed to be part of the ini
        bank_certPath = os.path.join(self._bankconfig.path(), "bank.cert")
        self._bank_cert = loadCertFromFile(bank_certPath)
        
    def set_src_account(self, src_account):
        """This is not async. should be called before loop starts or in executor"""
        self._login_name = input("Enter bank login name for account {}: ".format(src_account))
        self._password   = getpass.getpass("Password: ")
        self._src_account=src_account
        
    async def make_payment(self, dst_account, amount, memo):
        loop = asyncio.get_event_loop()
        bank_addr = self._bankconfig.get_parameter("CLIENT","bank_addr")
        bank_port = int(self._bankconfig.get_parameter("CLIENT","bank_port"))
        
        print("Connect to bank {}:{} for payment.".format(bank_addr, bank_port))
        
        transport, protocol = await playground.create_connection(
            lambda: BankClientProtocol(self._bank_cert, self._login_name, self._password),
            bank_addr,
            bank_port)
        try:
            result = await protocol.loginToServer()
        except Exception as e:
            print("Could not log in because", e)
            self.transport.close()
            return None
        
        try:
            result = await protocol.switchAccount(self._src_account)
            result = await protocol.transfer(dst_account, amount, memo)
        except Exception as e:
            result = None
            print("Could not transfer funds because", e)
        
        try:
            protocol.close()
        except Exception as e:
            print ("Warning, could not close bank connection because", e)
        return result
global_payment_processor = PaymentProcessing()

async def async_get_input(prompt):
    print(prompt, end="")
    sys.stdout.flush()
    while len(input_queue) == 0:
        await asyncio.sleep(.1)
    return input_queue.pop(0)
    
def stdin_reader():
    line_in = sys.stdin.readline()
    input_queue.append(line_in[:-1])

class EscapeRoomClientProtocol(asyncio.Protocol):
    def __init__(self):
        self._buffer = PacketType.Deserializer()
        self._token = None
        
    def connection_made(self, transport):
        self.transport = transport
        self.transport.write(RequestGame().__serialize__())
        print("request game sent")
    
    def connection_lost(self, transport):
        loop = asyncio.get_event_loop()
        
        # 1 second to shut everything down.
        loop.call_later(1, loop.stop)
        
    def data_received(self, data):
        self._buffer.update(data)
        for packet in self._buffer.nextPackets():
            print("Client got", packet)
            if isinstance(packet, RequestAdmission):
                if self._token != None:
                    self.transport.close()
                    raise Exception("Already paid!")
                else:
                    self._token = packet.token
                    make_payment_coro = self.pay_for_admission(
                        packet.account,
                        packet.amount,
                        packet.token)
                    asyncio.ensure_future(make_payment_coro)
            elif isinstance(packet, PaymentResult):
                if not packet.accepted:
                    print("Payment rejected: ", packet.accepted)
                    self.transport.close()
                else:
                    print("Starting game.")
                    asyncio.ensure_future(self.get_escape_room_input())
            elif isinstance(packet, GameResponse):
                print(packet.response)
                if packet.status == "locked":
                    asyncio.ensure_future(self.get_escape_room_input())
                elif packet.status == "escaped":
                    print("Congratulations! You escaped!")
                    self.transport.close()
                else:
                    print("Sorry! You died!")
                    self.transport.close()
                
    async def pay_for_admission(self, dst_account, amount, token):
        
        result = await global_payment_processor.make_payment(dst_account, amount, token)
        if result == None:
            self.transport.close()
            return False
            
        proof = ProofOfPayment(
            token    =self._token,
            receipt  =result.Receipt, 
            signature=result.ReceiptSignature)
            
        self.transport.write(proof.__serialize__())
        return True

    async def response(self):
        while not self.server_response:
            await asyncio.sleep(.1)
        r = self.server_response
        self.server_response = None
        return r

    async def get_escape_room_input(self):
        command = await async_get_input(">> ")
        cmd = GameRequest(token=self._token, command=command)
        self.transport.write(cmd.__serialize__())
        
if __name__=="__main__":
    import sys, argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument("account")
    parser.add_argument("--host", default="localhost")
    parser.add_argument("-p", "--port", default=5678)
    
    args = parser.parse_args(sys.argv[1:])
    host, port = args.host, args.port
    port = int(port)
    
    # this will ask for login name and password for bank for this account
    # but it doesn't actually log in yet.
    global_payment_processor.set_src_account(args.account)
    
    loop = asyncio.get_event_loop()
    coro = playground.create_connection(EscapeRoomClientProtocol, host=host, port=port)
    transport, protocol = loop.run_until_complete(coro)
    print("connected",protocol,transport)
    loop.add_reader(sys.stdin, stdin_reader)
    loop.run_forever()
    loop.close()