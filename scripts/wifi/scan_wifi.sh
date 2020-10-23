#!/bin/sh

# globals
PROG_NAME="$(basename "${0}")"
DEVICE="wlan0"

# functions
usage () {
	echo "${PROG_NAME}:"
	echo "    -h|--help                         :display this help"
	echo "    -d|--device                       :wifi device to scan (default: wlan0)"
	exit 1
}

# main
options=$(getopt -l "help,device:" -o "hd:" -- "${@}")
eval set -- "${options}"

while true
do
	case "${1}" in
		-h|--help )
			usage
			;;
		-d|--device )
			shift
			DEVICE="${1}"
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

iw dev "${DEVICE}" scan | awk \
'BEGIN {
}
/^BSS / {
	MAC = substr($2,1,17)
	wifi[MAC]["mac"] = MAC
	wifi[MAC]["enc"] = "Open"
}
/SSID:/ {
	if ($2 == "")
		wifi[MAC]["SSID"] = "hidden"
	else
		wifi[MAC]["SSID"] = $2
}
/freq:/ {
	wifi[MAC]["freq"] = $2
}
/signal:/ {
	wifi[MAC]["sig"] = $2 " " $3
}
/WPA:/ {
	wifi[MAC]["enc"] = "WPA"
}
/WEP:/ {
	wifi[MAC]["enc"] = "WEP"
}
END {
    printf "%-20s%-20s%-10s%-15s%-10s\n","0SSID","MAC","Frequency","Signal","Encryption"

    for (w in wifi) {
        printf "%-20s%-20s%-10s%-15s%-10s\n",wifi[w]["SSID"],wifi[w]["mac"],wifi[w]["freq"],wifi[w]["sig"],wifi[w]["enc"]
    }
}'
