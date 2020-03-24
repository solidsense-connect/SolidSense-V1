# Copyright 2019 Wirepas Ltd licensed under Apache License, Version 2.0
#
# See file LICENSE for full license details.

import os
import sys
from datetime import datetime

from wirepas_gateway.dbus.dbus_client import BusClient
from wirepas_gateway.utils import LoggerHelper


class SinkConfigurator(BusClient):
    """
    Simple class example that print all received message from dbus
    """
    def __init__(self, **kwargs):
        super(SinkConfigurator, self).__init__(**kwargs)


    def on_data_received(
        self,
        sink_id,
        timestamp,
        src,
        dst,
        src_ep,
        dst_ep,
        travel_time,
        qos,
        hop_count,
        data,
    ):
        """ logs incoming data from the WM network """
        self.logger.info(
            "[%s] Sink %s FROM %d TO %d on EP %d Data Size is %d",
            datetime.utcfromtimestamp(int(timestamp / 1000)).strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
            sink_id,
            src,
            dst,
            dst_ep,
            len(data),
        )

    def on_sink_connected(self, name):
        sink = self.sink_manager.get_sink(name)

        if sink is not None:
            # Read Stack status of sink on connection
            self.logger.info("Sink connected with config: %s", sink.read_config())

def print_sink(sink):
        # sink= obj.sink_manager.get_sink(name)
        if sink is not None :
            sink_conf=sink.read_config()
            # print(sink_conf)
            name=sink_conf['sink_id']
            network_id=sink_conf['network_address']
            network_channel=sink_conf['network_channel']
            sink_address=sink_conf['node_address']
            started=sink_conf['started']
            if started:
                stack="Started"
            else:
                stack= "Stopped"
            print("Sink",name,"Network:",network_id,"Channel:",network_channel,"Address:",sink_address,"Stack",stack)

def stackActivity(sink,start) :
        config={}
        config['started']=start
        sink.write_config(config)


def main():

    # Set default debug level
    debug_level = "info"

    log = LoggerHelper(module_name=__name__, level=debug_level)
    logger = log.setup()


    obj = SinkConfigurator()
    obj.logger = logger

    sinks=obj.sink_manager.get_sinks()
    for sink in sinks:
        print_sink(sink)
    if len(sys.argv) > 1 :
        cmd=sys.argv[1].lower()
        if cmd ==  "start" :
            start=True
        elif cmd == "stop" :
            start = False
        else:
            print("Unknow command")
            return
        for sink in sinks:
            stackActivity(sink,start)
            print_sink(sink)


if __name__ == "__main__":

    main()
