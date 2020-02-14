#!/bin/sh

# Glocal variables
PROG_NAME="$(basename "${0}")"
NODE_ADDRESS="1"
NODE_ROLE=""
NETWORK_ADDRESS="1000512"
NETWORK_CHANNEL="15"
SINK_NAME="sink1"
SINK_START="0"
CONFIG_OPTS=""

# functions
usage () {
	echo "${PROG_NAME}:"
	echo "    -h|--help"
	echo "    -n|--node-address                             : Node Address"
	echo "    -r|--node-role                                : Node Role"
	echo "    -N|--network-address                          : Network address"
	echo "    -c|--network-channel                          : Network channel"
	echo "    -s|--sink-name                                : Sink name"
	echo "    -S|--start                                    : Start the sink after configuration"
	echo ""
	exit 1
}

# main
options=$(getopt -l "help,node-address:,node-role:,network-address:,network-channel:,sink-name:,start" -o "hn:r:N:c:s:S" -- "${@}")
eval set -- "${options}"

while true
do
	case "${1}" in
		-h|--help )
			usage
			;;
		-n|--node-address )
			shift
			NODE_ADDRESS="${1}"
			;;
		-r|--node-role )
			shift
			NODE_ROLE="${1}"
			;;
		-N|--network-address )
			shift
			NETWORK_ADDRESS="${1}"
			;;
		-c|--network-channel )
			NETWORK_CHANNEL="${1}"
			shift
			;;
		-s|--sink-name )
			shift
			SINK_NAME="${1}"
			;;
		-S|--start )
			SINK_START="1"
			;;
		\? )
			usage
			;;
		: )
			echo "Invalid option: ${OPTARG} requires an arguemnt" 1>&2
			;;
		-- )
			shift
			break
			;;
		* )
			usage
			;;
	esac
	shift
done

# Build options to pass to configure_node.py
CONFIG_OPTS="-n ${NODE_ADDRESS} -N ${NETWORK_ADDRESS} -c ${NETWORK_CHANNEL} -s ${SINK_NAME}"
if [ -n "${NODE_ROLE}" ]; then
	CONFIG_OPTS="${CONFIG_OPTS} -r ${NODE_ROLE}"
fi
if [ "${SINK_START}" = "1" ]; then
	CONFIG_OPTS="${CONFIG_OPTS} -S"
fi
sudo --user=solidsense python3 /opt/SolidSense/wirepas/configure_node.py ${CONFIG_OPTS}
