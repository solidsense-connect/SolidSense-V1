# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:       Wirepas gRPC client for test and demo
# Purpose:
#              Shall run on LInux only
#
# Author:      Laurent Carre
#
# Created:     15/07/2019
# Copyright:   (c) Laurent Carre - Sterwen Technology 2019
# Licence:
#-------------------------------------------------------------------------------

import datetime

import grpc

from   grpc_service_pb2 import *
import grpc_service_pb2_grpc


def run():
    # NOTE(gRPC Python Team): .close() is possible on a channel and should be
    # used in circumstances in which the with statement does not fit the needs
    # of the code.
    with grpc.insecure_channel('127.0.0.1:9883') as channel:
        stub = grpc_service_pb2_grpc.WirepasConnectorStub(channel)

        # send packet demo
        print("Sending a packet to node 5 ...")
        packet = SendPacketReq()
        packet.destination_address = 5
        packet.source_endpoint = 0
        packet.destination_endpoint = 0
        packet.qos = 0
        packet.payload = b'GO'
        response = stub.SendPacket(packet)
        print("Packet sent")

        # receive packets demo
        print("Waiting for incoming packets - CTRL-C to exit")
        for packet in stub.GetPackets(VoidParameter()):
            print("[{}] ADDRESS FROM {} TO {} - EP FROM {} TO {} - Data Size is {}".format(
                  datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                  packet.source_address,
                  packet.destination_address,
		  packet.source_endpoint,
		  packet.destination_endpoint,
                  len(packet.payload)
            ))



if __name__ == '__main__':
    run()
