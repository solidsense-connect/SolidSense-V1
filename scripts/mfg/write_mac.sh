#!/bin/bash

# Globals
PROG_NAME="$(basename "${0}")"
MAC0="/sys/fsl_otp/HW_OCOTP_MAC0"
MAC1="/sys/fsl_otp/HW_OCOTP_MAC1"

# Functions
usage () {
	echo "${PROG_NAME} <MAC ADDRESS>"
	echo ""
	echo "    example: ${PROG_NAME} D063B40253EF"
	exit 1
}

check_mac_otp_files () {
	for file in ${MAC0} ${MAC1} ; do
		if [ -f "${file}" ] ; then
			chmod u+w "${file}"
		else
			echo "File not found! <${file}>"
			exit 1
		fi
	done
}

get_mac1 () {
	printf "0x%X\n" "$(( ((0x${MAC:0:2} & 0xFF) << 8) | (0x${MAC:2:2} & 0xFF) ))"
}

get_mac0 () {
	printf "0x%X\n" "$(( ((0x${MAC:4:2} & 0xFF) << 24) | ((0x${MAC:6:2} & 0xFF) << 16) | \
		((0x${MAC:8:2} & 0xFF) << 8) | (0x${MAC:10:2} & 0xFF) ))"
}

# Main
if [ $# -ne 1 ] ; then
	usage
else
	MAC="${1}"
fi

#check_mac_otp_files
#get_mac1 > "${MAC1}"
#get_mac0 > "${MAC0}"
get_mac1
get_mac0
