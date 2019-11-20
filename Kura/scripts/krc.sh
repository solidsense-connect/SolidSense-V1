#!/bin/sh

LOG="/usr/bin/logger -t kura krc:"
CMD="${*}"

export PATH=/bin:/sbin:/usr/bin:/usr/sbin

${LOG} "running command: ${*}"
cmd_output=$(${CMD})
cmd_rv="${?}"
if [ "${cmd_rv}" -eq 0 ] && [ -z "${cmd_output}" ]
then
	echo "Success!"
else
	echo "${cmd_output}"
fi

exit 0
