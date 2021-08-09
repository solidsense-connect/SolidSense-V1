#!/bin/bash

# Globals
PROG_NAME="$(basename "${0}")"
RPMB_DEVICE="/dev/mmcblk2rpmb"
PART=""
SERIAL=""
PRODUCT=""
SINK1_TYPE=""
STACK1_TYPE=""
SW1_VERSION=""
SINK2_TYPE=""
STACK2_TYPE=""
SW2_VERSION=""
rpmb_key_base64=""
rpmb_key_file="$(mktemp /tmp/rpmb_key.XXXXXXXX)"
rpmb_data_file="$(mktemp /tmp/rpmb_data.XXXXXXXX)"
RPMB_READ=0

#
AWK="$(command -vp awk)"
BASE64="$(command -vp base64)"
DD="$(command -vp dd)"
MMC="$(command -vp mmc)"
TR="$(command -vp tr)"
WC="$(command -vp wc)"

# Functions
usage () {
	echo "${PROG_NAME}"
	echo ""
	echo "    -h|--help"
	echo "    -N|--part <part number>"
	echo "    -S|--serial <serial>"
	echo "    -C|--product <product code>"
	echo "    -1|--sink1-type <type>"
	echo "    -2|--stack1-type <type>"
	echo "    -3|--sw1-version <version>"
	echo "    -4|--sink2-type <type>"
	echo "    -5|--stack2-type <type>"
	echo "    -6|--sw2-version <version>"
	echo "    -R|--rpmb-key <rpmb key>             : RPMB is base64 format"
	echo "    -r|--rpmb-read                       : Read current RPMB data"
	echo ""
	echo "DEFAULTS:"
	echo "    Part Number: ${PART}"
	echo "    Serial: ${SERIAL}"
	echo "    Product Code: ${PRODUCT}"
	echo "    Sink1 type: ${SINK1_TYPE}"
	echo "    Stack1 type: ${STACK1_TYPE}"
	echo "    Sink1 version: ${SW1_VERSION}"
	echo "    Sink2 type: ${SINK2_TYPE}"
	echo "    Stack1 type: ${STACK2_TYPE}"
	echo "    Sink2 version: ${SW2_VERSION}"
	echo "    RPMB Key: ${rpmb_key_base64}"
	exit 1
}

check_commands () {
	do_exit=0

	for file in "${AWK:-awk}" "${DD:-dd}" "${BASE64:-base64}" "${MMC:-mmc}" "${TR:-tr}" "${WC:-wc}" ; do
		if [ ! -f "${file}" ] ; then
			echo "Command: <${file}> not found!"
			do_exit=1
		fi
	done

	if [ "${do_exit}" -eq 1 ] ; then
		exit 1
	fi
}

read_rpmb () {
	mmc_output="$(${MMC} rpmb read-block ${RPMB_DEVICE} 0x0 1 - | sed 's/,/ /g' | tr -s '\0' '\n')"

	echo "Values for RPMB:"
	printf "%15s %15s %15s\n" "Key" "New Value" "Old Value"
	for entry in ${mmc_output}
	do
		rpmb_key=${entry%=*}
		rpmb_val=${entry#*=}
		new_key_value=$(eval "echo \$${rpmb_key}")
		declare -g -x "${rpmb_key}"="${new_key_value}"
		if [ -z "${new_key_value}" ] ; then
			declare -g -x "${rpmb_key}"="${rpmb_val}"
		fi
		printf "%15s %15s %15s\n" "${rpmb_key}" "$(eval "echo \$${rpmb_key}")" "${rpmb_val}"
	done
}

write_rpmb () {
	DATA="PART=${PART},SERIAL=${SERIAL},PRODUCT=${PRODUCT},SINK1_TYPE=${SINK1_TYPE},STACK1_TYPE=${STACK1_TYPE},SW1_VERSION=${SW1_VERSION}"

	if [ -n "${SINK2_TYPE}" ] ; then
		tmp_var="${DATA},SINK2_TYPE=${SINK2_TYPE},STACK2_TYPE=${STACK2_TYPE},SW2_VERSION=${SW2_VERSION}"
		DATA="${tmp_var}"
	fi

	tmp_var="${DATA^^}"
	DATA="${tmp_var}"

	# write temporary files
	echo -n "${DATA}" > "${rpmb_data_file}"
	echo -n "${rpmb_key_base64}" | ${BASE64} --decode - > "${rpmb_key_file}"

	# Pad out rpmb data
	BYTES=$(( 256-$(${WC} -c "${rpmb_data_file}" | ${AWK} '{print $1}') ))
	${DD} if=/dev/zero bs=1 count="${BYTES}" >> "${rpmb_data_file}" 2> /dev/null

	# Write the RPMB key
	printf "Writing the RPMB key\n"
	${MMC} rpmb write-key "${RPMB_DEVICE}" "${rpmb_key_file}" > /dev/null 2>&1

	# Write the RPMB data
	printf "Writing the following to the RPMB: \n%s\n\n" "${DATA}"
	${MMC} rpmb write-block "${RPMB_DEVICE}" 0x0 "${rpmb_data_file}" "${rpmb_key_file}"

	# Verify the RPMB data
	DATA_READ="$(${MMC} rpmb read-block ${RPMB_DEVICE} 0x0 1 - | tr -s '\0' '\n')"
	if [ "${DATA}" != "${DATA_READ}" ] ; then
		echo "Written value does not equal read value!"
		echo "written: ${DATA}"
		echo "read   : ${DATA_READ}"
	fi
}

clean_up () {
	for file in ${rpmb_key_file} ${rpmb_data_file} ; do
		if [ -f "${file}" ]; then
			rm -f "${file}"
		fi
	done
}

# Main
options=$(getopt -l "help,part:,serial:,product:,sink1-type:,stack1-type:,sw1-version:,sink2-type:,stack2-type:,sw2-version:,rpmb-key:,rpmb-read" -o ":hN:S:C:1:2:3:4:5:6:R:r" -- "${@}")
eval set -- "${options}"

while true
do
	case ${1} in
		-h|--help )
			usage
			;;
		-N|--part )
			shift
			PART="${1}"
			;;
		-S|--serial )
			shift
			SERIAL="${1}"
			;;
		-C|--product )
			shift
			PRODUCT="${1}"
			;;
		-1|--sink1-type )
			shift
			SINK1_TYPE="${1}"
			;;
		-2|--stack1-type )
			shift
			STACK1_TYPE="${1}"
			;;
		-3|--sw1-version )
			shift
			SW1_VERSION="${1}"
			;;
		-4|--sink2-type )
			shift
			SINK2_TYPE="${1}"
			;;
		-5|--stack2-type )
			shift
			STACK2_TYPE="${1}"
			;;
		-6|--sw2-version )
			shift
			SW2_VERSION="${1}"
			;;
		-R|--rpmb-key )
			shift
			rpmb_key_base64="${1}"
			;;
		-r|--rpmb-read )
			RPMB_READ=1
			;;
                \? )
                        usage
                        ;;
                : )
                        echo "Invalid option: ${OPTARG} requires an argument" 1>&2
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

if [ -z "${rpmb_key_base64}" ] ; then
	echo "-R|--rpmb-key is a mandatory option"
	usage
fi

check_commands
if [ "${RPMB_READ}" -eq 1 ] ; then
	read_rpmb
fi

echo "Do you wish to write to the RPMB? (Y|N)"
read -r answer

if [ "${answer}" = "Y" ] ; then
	write_rpmb
elif [ "${answer}" = "N" ] ; then
	exit 0
else
	echo "Please use either Y or N!"
	exit 1
fi
clean_up
