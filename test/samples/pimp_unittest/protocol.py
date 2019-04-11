import sys
sys.path.append("../../../../src/reliable_layers/")
from y20191_pimp.protocol import PimpClientProtocol, PimpServerProtocol, PIMPPacket
from playground.network.testing.mock import MockTransportToStorageStream as MockTransport
from playground.asyncio_lib.testing import TestLoopEx
from playground.common.logging import EnablePresetLogging, PRESET_DEBUG
from unittest.mock import MagicMock
import unittest, io, asyncio, hashlib, os

def create_packet(**config):
    packet = PIMPPacket()
    packet.seqNum = config.get("seqNum", 0)
    packet.ackNum = config.get("ackNum", 0)
    packet.SYN    = config.get("SYN",False)
    packet.ACK    = config.get("ACK",False)
    packet.RST    = config.get("RST",False)
    packet.RTR    = config.get("RTR",False)
    packet.FIN    = config.get("FIN",False)
    packet.data   = config.get("data", b"")
    packet.checkSum = b""
    packet_bytes  = packet.__serialize__()
    packet.checkSum = hashlib.md5(packet_bytes).digest()
    return packet
    
class PacketStream:
    def __init__(self):
        self.packets = []
        
    def write(self, data):
        deserializer = PIMPPacket.Deserializer()
        deserializer.update(data)
        self.packets += list(deserializer.nextPackets())

class TestLegalCommands(unittest.TestCase):
    def setUp(self):
        self.loop = TestLoopEx()
        asyncio.set_event_loop(self.loop)
        self.client = PimpClientProtocol()
        self.client.setHigherProtocol(MagicMock())
        self.client_transport = MockTransport(PacketStream())
        self.server = PimpServerProtocol()
        self.server.setHigherProtocol(MagicMock())
        self.server_transport = MockTransport(PacketStream())
        
    def tearDown(self):
        self.loop.close()
        
    def test_normal_handshake_client(self):
        
        # create connection. should send SYN
        self.client.connection_made(self.client_transport)
        
        self.assertEqual(len(self.client_transport.sink.packets), 1)
        client_syn = self.client_transport.sink.packets.pop(0)
        self.assertTrue(client_syn.SYN)
        
        # create server response with SYN_ACK.
        # ackNum = client seqNum + 1
        server_seqNum = 300
        syn_ack_packet = create_packet(
            seqNum=server_seqNum, 
            ackNum=client_syn.seqNum+1, 
            SYN=True,
            ACK=True)
        self.client.data_received(syn_ack_packet.__serialize__())
        
        # at this point, the entire handshake should be over.
        # check and client transmissions
        self.assertEqual(len(self.client_transport.sink.packets), 1)
        client_ack = self.client_transport.sink.packets.pop(0)

        self.assertTrue(client_ack.ACK)
        self.assertEqual(client_ack.ackNum, server_seqNum+1)
        
        # verify that higher protocol's connection made was called
        self.client.higherProtocol().connection_made.assert_called()
        
    def test_handshake_client_on_client_crash(self):
        
        # create connection. should send SYN
        self.client.connection_made(self.client_transport)
        
        self.assertEqual(len(self.client_transport.sink.packets), 1)
        client_syn = self.client_transport.sink.packets.pop(0)
        self.assertTrue(client_syn.SYN)
        
        # create server response ASSUMING server was not in listening state.
        # this is based on example in PRFC after client crash
        # pick arbitrary sequence number and ack number
        server_syn = 400
        server_ack = 100
        bad_ack_packet = create_packet(
            seqNum=server_syn, 
            ackNum=server_ack,
            ACK=True)
        self.client.data_received(bad_ack_packet.__serialize__())
        
        self.assertEqual(len(self.client_transport.sink.packets) > 0)
        client_rst = self.client_transport.sink.packets.pop(0)
        self.assertTrue(client_rst.RST)
        self.assertEqual(client_rst.seqNum, server_ack)
        
        # client should resend SYN
        self.loop.advanceClock(10)
        
        # various student implementations might have
        # multiple functions that trigger once, sending
        # multiple packets. simply check if the first
        # packet is the SYN
        self.assertTrue(len(self.client_transport.sink.packets) > 0)
        client_syn2 = self.client_transport.sink.packets.pop(0)
        self.assertTrue(client_syn2.SYN)
        
    def test_normal_handshake_server(self):
        
        # create server
        self.server.connection_made(self.server_transport)
        
        # create client SYN.
        client_seqNum = 300
        syn_packet = create_packet(seqNum=client_seqNum, SYN=True)
        self.server.data_received(syn_packet.__serialize__())
        
        # server should have sent a syn,ack.
        self.assertEqual(len(self.server_transport.sink.packets), 1)
        server_syn_ack = self.server_transport.sink.packets.pop(0)
        self.assertTrue(server_syn_ack.SYN)
        self.assertTrue(server_syn_ack.ACK)
        self.assertEqual(server_syn_ack.ackNum, client_seqNum+1)

        # send ack to trigger session establishment
        ack_packet = create_packet(
            seqNum=client_seqNum+1, 
            ackNum=server_syn_ack.seqNum+1, 
            ACK=True)
        self.server.data_received(ack_packet.__serialize__())
        
        # at this point, server should have called connection_made
        self.server.higherProtocol().connection_made.assert_called()
        
    def test_handshake_server_on_client_crash(self):
        # create server
        self.server.connection_made(self.server_transport)
        
        # create client SYN.
        client_seqNum = 400
        syn_packet = create_packet(seqNum=client_seqNum, SYN=True)
        self.server.data_received(syn_packet.__serialize__())
        
        # server should have sent a syn,ack.
        self.assertEqual(len(self.server_transport.sink.packets), 1)
        server_syn_ack = self.server_transport.sink.packets.pop(0)
        self.assertTrue(server_syn_ack.SYN)
        self.assertTrue(server_syn_ack.ACK)
        self.assertEqual(server_syn_ack.ackNum, client_seqNum+1)

        # create new client SYN after crash.
        # pick a sequence number outside of window
        client_seqNum2 = 300
        syn2_packet = create_packet(seqNum=client_seqNum2, SYN=True)
        self.server.data_received(syn2_packet.__serialize__())
        
        # server should send an ACK with old seq num + 1
        self.assertEqual(len(self.server_transport.sink.packets), 1)
        server_ack = self.server_transport.sink.packets.pop(0)
        self.assertTrue(server_ack.ACK)
        self.assertEqual(server_ack.ackNum, client_seqNum+1)
        
        # send client RST
        rst_packet = create_packet(seqNum=server_ack.ackNum, RST=True)
        self.server.data_received(rst_packet.__serialize__())
        
        # resend client post-crash syn
        self.server.data_received(syn2_packet.__serialize__())
        self.assertEqual(len(self.server_transport.sink.packets), 1)
        server_syn_ack = self.server_transport.sink.packets.pop(0)
        self.assertTrue(server_syn_ack.SYN)
        self.assertTrue(server_syn_ack.ACK)
        self.assertEqual(server_syn_ack.ackNum, client_seqNum2+1)
        
    def test_no_error_data_transmission(self):
        # connect the client and server
        self.server.connection_made(self.server_transport)
        self.client.connection_made(self.client_transport)
        
        # handle syn
        self.assertEqual(len(self.client_transport.sink.packets), 1)
        syn_packet = self.client_transport.sink.packets.pop(0)
        self.assertTrue(syn_packet.SYN)
        self.server.data_received(syn_packet.__serialize__())
        
        # handle syn_ack
        self.assertEqual(len(self.server_transport.sink.packets), 1)
        syn_ack_packet = self.server_transport.sink.packets.pop(0)
        self.assertTrue(syn_ack_packet.SYN)
        self.assertTrue(syn_ack_packet.ACK)
        self.client.data_received(syn_ack_packet.__serialize__())
        
        # handle ack
        self.assertEqual(len(self.client_transport.sink.packets), 1)
        ack_packet = self.client_transport.sink.packets.pop(0)
        self.assertTrue(ack_packet.ACK)
        self.server.data_received(ack_packet.__serialize__())
        
        self.client.higherProtocol().connection_made.assert_called()
        self.server.higherProtocol().connection_made.assert_called()
        
        client_app_transport, = self.client.higherProtocol().connection_made.call_args[0]
        server_app_transport, = self.server.higherProtocol().connection_made.call_args[0]
        
        # transmissions
        # 1 byte
        # 16 bytes
        # 1024 bytes
        # 10240 bytes
        
        transmissions = [os.urandom(size) for size in [1,16,1024,10240]]
        
        # simulate testing full duplex
        # monitor the data as it goes from one side to the other
        # To prevent infinite loop, error on duplicate ack
        # and error if seq number is greater than transmission
        # this assumes that acks are sent without timeouts.
        # if your implementation requires timeouts in 0 error
        # conditions, please contact us
        client_last_ack = 0
        server_last_ack = 0
        client_max_seq = syn_packet.seqNum + 1
        server_max_seq = syn_ack_packet.seqNum + 1
        for transmission in transmissions:
            client_app_transport.write(transmission)
            server_app_transport.write(transmission)
            client_max_seq += len(transmission)
            server_max_seq += len(transmission)
            
            # keep sending packets until all data transmitted.
            # see message above about preventing infinite loop
            
            while self.client_transport.sink.packets or self.server_transport.sink.packets:
                if self.client_transport.sink.packets:
                    client_packet = self.client_transport.sink.packets.pop(0)
                    if client_packet.data:
                        self.assertTrue(client_packet.seqNum < client_max_seq)
                    
                    if not client_packet.data and client_packet.ACK:
                        self.assertTrue(client_packet.ackNum > client_last_ack)
                        client_last_ack = client_packet.ackNum
                    self.server.data_received(client_packet.__serialize__())
                        
                if self.server_transport.sink.packets:
                    server_packet = self.server_transport.sink.packets.pop(0)
                    if server_packet.data:
                        self.assertTrue(server_packet.seqNum < server_max_seq)
                    
                    if not server_packet.data and server_packet.ACK:
                        self.assertTrue(server_packet.ackNum > server_last_ack)
                        server_last_ack = server_packet.ackNum
                
                    self.client.data_received(server_packet.__serialize__())
        
        clientapp_data_received = self.client.higherProtocol().data_received.call_args_list
        serverapp_data_received = self.server.higherProtocol().data_received.call_args_list
        for transmission in transmissions:
            client_data = b""
            while len(client_data) < len(transmission) and clientapp_data_received:
                client_data += clientapp_data_received.pop(0)[0][0]
            self.assertEqual(transmission, client_data)
            
            server_data = b""
            while len(server_data) < len(transmission) and serverapp_data_received:
                server_data += serverapp_data_received.pop(0)[0][0]
            self.assertEqual(transmission, server_data)
            
    def test_client_shutdown_no_errors(self):
        # connect the client and server
        self.server.connection_made(self.server_transport)
        self.client.connection_made(self.client_transport)
        
        # handle syn
        self.assertEqual(len(self.client_transport.sink.packets), 1)
        syn_packet = self.client_transport.sink.packets.pop(0)
        self.assertTrue(syn_packet.SYN)
        self.server.data_received(syn_packet.__serialize__())
        
        # handle syn_ack
        self.assertEqual(len(self.server_transport.sink.packets), 1)
        syn_ack_packet = self.server_transport.sink.packets.pop(0)
        self.assertTrue(syn_ack_packet.SYN)
        self.assertTrue(syn_ack_packet.ACK)
        self.client.data_received(syn_ack_packet.__serialize__())
        
        # handle ack
        self.assertEqual(len(self.client_transport.sink.packets), 1)
        ack_packet = self.client_transport.sink.packets.pop(0)
        self.assertTrue(ack_packet.ACK)
        self.server.data_received(ack_packet.__serialize__())
        
        self.client.higherProtocol().connection_made.assert_called()
        self.server.higherProtocol().connection_made.assert_called()
        
        client_app_transport, = self.client.higherProtocol().connection_made.call_args[0]
        server_app_transport, = self.server.higherProtocol().connection_made.call_args[0]
        
        server_app_transport.write(b"server transmission")
        
        self.assertEqual(len(self.server_transport.sink.packets), 1)
        server_data_packet = self.server_transport.sink.packets.pop(0)
        
        self.client.data_received(server_data_packet.__serialize__())
        
        client_app_transport.close()
        self.client.higherProtocol().connection_lost.assert_called()
        
        # there could be multiple acks, check that last packet is fin
        self.assertTrue(len(self.client_transport.sink.packets)>= 1)
        fin_packet = self.client_transport.sink.packets.pop(-1)
        self.assertTrue(fin_packet.FIN)
        
        # We aren't even testing all the states. Just test whether
        # or not we call server connection_lost.
        self.server.data_received(fin_packet.__serialize__())
        self.server.higherProtocol().connection_lost.assert_called()
        
    def test_reordering(self):
        # connect the client and server
        self.server.connection_made(self.server_transport)
        self.client.connection_made(self.client_transport)
        
        # handle syn
        self.assertEqual(len(self.client_transport.sink.packets), 1)
        syn_packet = self.client_transport.sink.packets.pop(0)
        self.assertTrue(syn_packet.SYN)
        self.server.data_received(syn_packet.__serialize__())
        
        # handle syn_ack
        self.assertEqual(len(self.server_transport.sink.packets), 1)
        syn_ack_packet = self.server_transport.sink.packets.pop(0)
        self.assertTrue(syn_ack_packet.SYN)
        self.assertTrue(syn_ack_packet.ACK)
        self.client.data_received(syn_ack_packet.__serialize__())
        
        # handle ack
        self.assertEqual(len(self.client_transport.sink.packets), 1)
        ack_packet = self.client_transport.sink.packets.pop(0)
        self.assertTrue(ack_packet.ACK)
        self.server.data_received(ack_packet.__serialize__())
        
        self.client.higherProtocol().connection_made.assert_called()
        self.server.higherProtocol().connection_made.assert_called()
        
        client_app_transport, = self.client.higherProtocol().connection_made.call_args[0]
        server_app_transport, = self.server.higherProtocol().connection_made.call_args[0]
        
        client_app_transport.write(b"message 1")
        client_app_transport.write(b"message 2")
        client_app_transport.write(b"message 3")
        
        # there should be three packets
        self.assertEqual(len(self.client_transport.sink.packets), 3)
        data1, data2, data3 = self.client_transport.sink.packets
        self.client_transport.sink.packets = []

        # packets in reverse order
        self.server.data_received(data3.__serialize__())
        self.server.data_received(data2.__serialize__())
        
        self.server.higherProtocol().data_received.assert_not_called()
        
        self.server.data_received(data1.__serialize__())
        serverapp_data_received = self.server.higherProtocol().data_received.call_args_list
        serverdata = b""
        while serverapp_data_received:
            serverdata += serverapp_data_received.pop(0)[0][0]
        self.assertEqual(serverdata, b"message 1message 2message 3")
    
    def test_reordering_with_retransmit(self):
        self.test_reordering()
        # assume one re-transmit for each out-of-order message)
        self.assertEqual(len(self.server_transport.sink.packets),2)
        self.assertTrue(self.server_transport.sink.packets[0].RTR)
        self.assertTrue(self.server_transport.sink.packets[1].RTR)
        
if __name__ == '__main__':
    #EnablePresetLogging(PRESET_DEBUG)
    unittest.main()
