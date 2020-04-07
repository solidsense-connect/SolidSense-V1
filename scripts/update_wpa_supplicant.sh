#!/usr/bin/env bash

# globals
PROG_NAME="$(basename "${0}")"
WPA_CONF_FILE_TMP="/tmp/.wpa_supplicant-wlan0.conf"
WPA_CONF_FILE="/etc/wpa_supplicant-wlan0.conf"
CONF_TEMPLATE="$(mktemp /tmp/.wpa_supplicant-wlan0.conf.XXXXX)"
PARAMS=""
TEMPLATE=0

# functions

usage () {
	echo "${PROG_NAME}:"
	echo "    -h|--help                                  :display this help"
	echo "    -u|--username <username>                   :set username"
	echo "    -p|--password <password>                   :set password"
	echo "    -s|--ssid <ssid>                           :set ssid"
	echo "    -t|--template                              :whether to use template or update /etc/wpa_supplicant-wlan0.conf"
        echo "    -S|--show                                  :show current configure credentials"

	exit 1
}

create_wpa_supplicant_template () {
	# Create template
	cat > "${CONF_TEMPLATE}" << EOF
# allow frontend (e.g., wpa_cli) to be used by all users in 'wheel' group
ctrl_interface=/var/run/wpa_supplicant
#ctrl_interface_group=wheel

# home network; allow all valid ciphers
network={
    mode=0
    ssid="CHANGME"
    scan_ssid=1
    key_mgmt=WPA-EAP
    eap=PEAP
    identity=""
    password=""
    phase1="peaplabel=1"
    phase2="auth=MCHAPV2"
}
EOF
}

check_val () {
	arg="${1}"

	if [ -n "${arg}" ] ; then
		if echo "${arg}" | grep -q '^-'; then
			echo "Invalid argument: <${arg}>"
			usage
		fi
	fi

	return 0
}

update_wpa_supplicant_config () {
	if [ -n "${USERNAME}" ] ; then
		sed --in-place s/identity=.*/identity=\""${USERNAME}"\"/ ${WPA_CONF_FILE_TMP}
	fi
	if [ -n "${PASSWORD}" ] ; then
		sed --in-place s/password=.*/password=\""${PASSWORD}"\"/ ${WPA_CONF_FILE_TMP}
	fi
	if [ -n "${SSID}" ] ; then
		sed --in-place s/ssid=.*/ssid=\""${SSID}"\"/ ${WPA_CONF_FILE_TMP}
	fi
}

cleanup () {
	mv "${WPA_CONF_FILE_TMP}" "${WPA_CONF_FILE}"
	rm -f "${CONF_TEMPLATE}"
}

show_current_credentials () {
	USERNAME="$(awk '/identity="/ { sub(/^.*identity=/, ""); gsub(/\"/, ""); print}' < "${WPA_CONF_FILE}")"
	PASSWORD="$(awk '/password="/ { sub(/^.*password=/, ""); gsub(/\"/, ""); print}' < "${WPA_CONF_FILE}")"
	SSID="$(awk '/ssid="/ { sub(/^.*ssid=/, ""); gsub(/\"/, ""); print}' < "${WPA_CONF_FILE}")"

	echo "Configured username: <${USERNAME}>"
	echo "Configured password: <${PASSWORD}>"
	echo "Configured ssid: <${SSID}>"
}

# main

while (( "$#" ))
do
	case "${1}" in
		-h|--help )
			shift
			usage
			;;
		-S|--show )
			shift
			show_current_credentials
			exit 0
			;;
		-u|--username )
			USERNAME="${2}"
			shift 2
			check_val "${USERNAME}"
			;;
		-p|--password )
			PASSWORD="${2}"
			shift 2
			check_val "${PASSWORD}"
			;;
		-s|--ssid )
			SSID="${2}"
			shift 2
			check_val "${SSID}"
			;;
		-t|--template )
			shift
			TEMPLATE=0
			;;
		-- )
			shift
			break
			;;
		--*=|-* )
			echo "Error: Unsupported flag ${1}" >&2
			usage
			;;
		* )
			if [ -z "${PARAMS}" ]; then
				PARAMS="${1}"
			else
				PARAMS="${PARAMS} ${1}"
			fi
			shift
			;;
	esac
done

# Check if wpa supplicant config file exists

if [ ! -f "${WPA_CONF_FILE}" ]; then
	# need to create template
	TEMPLATE=0
fi

# Create template if required
if [ "${TEMPLATE}" -eq 0 ]; then
	create_wpa_supplicant_template
	mv "${CONF_TEMPLATE}" "${WPA_CONF_FILE_TMP}"
else
	cp "${WPA_CONF_FILE}" "${WPA_CONF_FILE_TMP}"
fi

# Update the wpa supplicant config
update_wpa_supplicant_config

# Cleanup, includes cp'ing the wpa_supplicant config in /tmp to /etc
cleanup
