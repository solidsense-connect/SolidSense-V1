# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:       gRPC Service for Wirepas
# Purpose:
#
#
# Author:      Nicolas Albarel
#
# Created:     15/07/2019
# Copyright:   (c) Laurent Carre - Sterwen Technology 2019
# Licence:
#-------------------------------------------------------------------------------

import os
import queue

from concurrent import futures
import grpc

from grpc_service_pb2 import *
import grpc_service_pb2_grpc

from threading import Thread, Lock

from wirepas_gateway.dbus.dbus_client import BusClient

import wirepas_messaging
from wirepas_messaging.gateway.api import GatewayResultCode, GatewayState, GatewayAPIParsingException

from wirepas_gateway.utils import LoggerHelper
from argument_tools import ParserHelper


# This constant is the actual API level implemented by this transport module (cf WP-RM-128)
IMPLEMENTED_API_VERSION = 1


class RpcStatus(object):
    def __init__(self, logger):
        self.logger = logger
        self.isAlive = True

    def RpcKilled(self):
        self.logger.info("listener killed")
        self.isAlive = False


class WirepasConnector(grpc_service_pb2_grpc.WirepasConnectorServicer):

    def __init__(self,
                 host,
                 port,
                 logger,
                 transport):
        self.logger = logger
        self.transport = transport

        self.server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        grpc_service_pb2_grpc.add_WirepasConnectorServicer_to_server(self, self.server)
        self.portConfig = '{}:{}'.format(host, port)
        self.server.add_insecure_port(self.portConfig)

        self.queue_list = []
        self.queue_lock = Lock()



    def GetPackets(self, request, context):
        self.logger.info("new packet listener")
        clientStatus = RpcStatus(self.logger)
        context.add_callback(clientStatus.RpcKilled)

        local_queue = queue.Queue()
        self.queue_lock.acquire()
        self.queue_list.append(local_queue)
        self.queue_lock.release()

        try:
            while clientStatus.isAlive and self.running:
                # Loop on the queue to be able to quit cleanly if client is leaving, or process exiting
                try:
                    packet = local_queue.get(timeout=1) # 1s timeout
                    yield packet

                except queue.Empty:
                    pass

        finally:
            self.logger.info("end of packet listener")
            self.queue_lock.acquire()
            self.queue_list.remove(local_queue)
            self.queue_lock.release()



    def SendPacket(self, request, context):
        self.transport._on_send_data_cmd_received(request)
        return VoidParameter()


    def start(self):
        self.running = True
        self.server.start()
        self.logger.info("gRPC service started on " + self.portConfig)

    def stop(self):
        self.running = False


    def ForwardPacket(self, packet):
        self.queue_lock.acquire()
        try:
            for q in self.queue_list:
               q.put_nowait(packet) # nowait not useful as Queue size is not limited, but use it for clarity
        finally:
            self.queue_lock.release()




class TransportService(BusClient):
    """
    """
    # Maximum hop limit to send a packet is limited to 15 by API (4 bits)
    MAX_HOP_LIMIT = 15

    def __init__(self,
                 host,
                 port,
                 logger=None,
                 c_extension=False,
                 ignored_endpoints_filter=None,
                 **kwargs):

        super(TransportService, self).__init__(
            logger=logger, c_extension=c_extension,
            ignored_ep_filter=ignored_endpoints_filter,
            **kwargs)

        self.connector = WirepasConnector(host, port, logger, self)
        self.connector.start()

        self.logger = logger or logging.getLogger(__name__)
        self.logger.info("Gateway started")



    def on_data_received(self, sink_id, timestamp, src, dst, src_ep, dst_ep, travel_time,
                         qos, hop_count, data):
        self.logger.debug("Data received from node {}".format(src))

        packet = PacketReceivedEvent()
        packet.source_address = src
        packet.destination_address = dst
        packet.source_endpoint = src_ep
        packet.destination_endpoint = dst_ep
        packet.travel_time_ms = travel_time
        packet.qos = qos
        packet.payload = data;
        packet.hop_count = hop_count

        self.connector.ForwardPacket(packet)



    def _on_send_data_cmd_received(self, request):
        self.logger.debug("Request to send data to node {}".format(request.destination_address))

        # Handle optional fields
        try:
            initial_delay_ms = request.initial_delay_ms
        except AttributeError:
            initial_delay_ms = 0

        try:
            is_unack_csma_ca = request.is_unack_csma_ca
        except AttributeError:
            is_unack_csma_ca = False

        try:
            hop_limit = request.hop_limit
        except AttributeError:
            hop_limit = 0



        if hop_limit > self.MAX_HOP_LIMIT:
            self.logger.warning("Invalid hop limit : {}".format(hop_limit))

        else:
            sinks = self.sink_manager.get_sinks()
            for sink in sinks:
                self.logger.debug("Send with sink id: {}".format(sink.sink_id))
                sink.send_data(request.destination_address,
                                     request.source_endpoint,
                                     request.destination_endpoint,
                                     request.qos,
                                     initial_delay_ms,
                                     request.payload,
                                     is_unack_csma_ca,
                                     hop_limit)

    def run(self):
        super().run() # Blocking call
        self.connector.stop()




def parse_setting_list(list_setting):
    """ This function parse ep list specified from setting file or cmd line

    Input list has following format [1, 5, 10-15] as a string or list of string
    and is expended as a single list [1, 5, 10, 11, 12, 13, 14, 15]

    Args:
        list_setting(str or list): the list from setting file or cmd line.

    Returns: A single list of ep
    """
    if isinstance(list_setting, str):
        # List is a string from cmd line
        list_setting = list_setting.replace('[', '')
        list_setting = list_setting.replace(']', '')
        list_setting = list_setting.split(',')

    single_list = []
    for ep in list_setting:
        # Check if ep is directly an int
        if isinstance(ep, int):
            if ep < 0 or ep > 255:
                raise SyntaxError("EP out of bound")
            single_list.append(ep)
            continue

        # Check if ep is a single ep as string
        try:
            ep = int(ep)
            if ep < 0 or ep > 255:
                raise SyntaxError("EP out of bound")
            single_list.append(ep)
            continue
        except ValueError as e:
            # Probably a range
            pass

        # Check if ep is a range
        try:
            lower, upper = ep.split('-')
            lower = int(lower)
            upper = int(upper)
            if lower > upper or \
                lower < 0 or \
                upper > 255:
                raise SyntaxError("Wrong EP range value")

            single_list += list(range(lower,upper + 1))
        except (AttributeError, ValueError):
            raise SyntaxError("Wrong EP range format")

    return single_list



def main():
    """
        Main service for transport module

    """
    parse = ParserHelper(description="Default arguments")

    parse.add_transport()
    parse.add_file_settings()

    args = parse.settings(skip_undefined=False)


    try:
        debug_level = os.environ['DEBUG_LEVEL']
    except KeyError:
        debug_level = 'debug'

    logger = LoggerHelper("transport_service")
    logger = logger.setup(level=debug_level)

    if args.full_python:
        logger.info("Starting transport without C optimisation")
        c_extension = False
    else:
        c_extension = True

    # Parse EP list that should not be published
    ignored_endpoints_filter = None
    if args.ignored_endpoints_filter is not None:
        try:
            ignored_endpoints_filter = parse_setting_list(args.ignored_endpoints_filter)
            logger.debug("Ignored endpoints are: {}".format(ignored_endpoints_filter))
        except SyntaxError as e:
            logger.error("Wrong format for ignored_endpoints_filter EP list ({})".format(e))
            exit()


    TransportService(args.host, args.port,
                     logger, c_extension,
                     ignored_endpoints_filter).run()


if __name__ == "__main__":
    """ executes main. """
    main()
