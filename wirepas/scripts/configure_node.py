# Copyright 2018 Wirepas Ltd. All Rights Reserved.
#
# See file LICENSE.txt for full license details.
#
import argparse
import logging
import sys

from wirepas_gateway.dbus.dbus_client import BusClient

root_logger = logging.basicConfig(stream=sys.stdout,level=logging.INFO)
local_log=logging.getLogger("Wirepas-Sink-Configuration")

class SinkConfigurator(BusClient):
    """
    Simple class to configure a sink
    """
    def __init__(self, **kwargs):
        super(SinkConfigurator, self).__init__(**kwargs)


    def configure(self, sink_name, node_address, node_role, network_address, network_channel, start, cypher, auth):
        sink = self.sink_manager.get_sink(sink_name)
        if sink is None:
            local_log.error("Cannot retrieve sink object:"+sink_name)
            return

        # Do the actual configuration
        config = {}
        if node_address is not None:
            config['node_address'] = node_address
        if node_role is not None:
            config['node_role'] = 17
        if network_address is not None:
            config['network_address'] = network_address
        if network_channel is not None:
            config['network_channel'] = network_channel
        if start is not None:
            config["started"] = start

        if cypher is not None:
            if len(cypher) != 16:
                local_log.error("Bad cypher key size "+ str(len(cypher)))
                return
            config["cipher_key"] = cypher

        if auth is not None:
            if len(auth) != 16:
                local_log.error("Bad authentication key size "+ str(len(auth)))
                return
            config["authentication_key"] = auth

        fmt="Requested Wirepas sink configuration for %s: %s"
        local_log.info(fmt%(sink_name,config))

        ret = sink.write_config(config)
        local_log.info("Configuration done with result = {}".format(ret))


def str2bool(v):
    if isinstance(v, bool):
       return v
    if v.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected.')

def str2bytes(value):
    """ Ensures string to bytes conversion """
	# NOTE: eval() is not safe, but the input is provided by a local user, so it could be trusted
    try:
        res = eval(value)
        if type(res) == bytes:
            return res
    except:
        pass

    raise argparse.ArgumentTypeError('Bytes value expected.')

def main(log_name='configure_node'):
    parser = argparse.ArgumentParser(fromfile_prefix_chars='@')
    parser.add_argument('-n',
                        '--node_address',
                        type=int,
                        help="Node address")

    parser.add_argument('-r',
                        '--node_role',
                        default=17, # LL Sink
                        type=int,
                        help="Node role")

    parser.add_argument('-N',
                        '--network_address',
                        type=int,
                        help="Network address")

    parser.add_argument('-c',
                        '--network_channel',
                        type=int,
                        help="Network channel")

    parser.add_argument('-s',
                        '--sink_name',
                        type=str,
                        help="Sink name")

    parser.add_argument('-S',
                        '--start',
                        type=str2bool,
                        help="Start the sink after configuration")

    parser.add_argument('-C',
                        '--cypher',
                        type=str2bytes,
                        help="Set Cypher Key")

    parser.add_argument('-A',
                        '--auth',
                        type=str2bytes,
                        help="Set Authentication Key")

    args = parser.parse_args()

    sink_configurator = SinkConfigurator()

    sink_configurator.configure(
        node_address=args.node_address,
        node_role=args.node_role,
        network_address=args.network_address,
        network_channel=args.network_channel,
        sink_name=args.sink_name,
        start=args.start,
        cypher=args.cypher,
        auth=args.auth)


if __name__ == "__main__":
    main()
