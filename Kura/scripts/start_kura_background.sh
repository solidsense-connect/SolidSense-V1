#!/bin/sh

# Kura should be installed to the /opt/eclipse directory.
export PATH=/bin:/usr/bin:/sbin:/usr/sbin:/usr/local/bin:/opt/jvm/bin:/usr/java/bin:$PATH
export MALLOC_ARENA_MAX=1
KURA_CUSTOM_PROPERTIES_FILE="/opt/eclipse/kura/user/kura_custom.properties"

# Create user snapshot_0.xml
if [ ! -f /opt/eclipse/kura/user/snapshots/snapshot_0.xml ] ; then
    cd "/opt/SolidSense/kura/config" || exit
    python3 /opt/SolidSense/kura/config/gen_kura_properties.py
fi

# Update kura_custom.properties
KURA_CUSTOM_PROPERTIES_FILE="/opt/eclipse/kura/user/kura_custom.properties"
KURA_CUSTOM_PROPERTIES_FILE_TMP="/tmp/kura_custom.properties"
NLINES=$(($(wc -l /opt/eclipse/kura/user/kura_custom.properties | awk '{print $1}') + 10))
MENDER_VERSION="$(sed s'/artifact_name=//' < /etc/mender/artifact_info)"
SOLIDSENSE_FILE="/etc/solidsense"
# shellcheck source=/dev/null
. ${SOLIDSENSE_FILE}

awk -v N="${NLINES}" -v MENDER_VERSION="${MENDER_VERSION}" -v SW1_VERSION="${SW1_VERSION}" -v SW2_VERSION="${SW2_VERSION}" \
'BEGIN {
	OLD_FS=FS
	FS="="
	NLINES=1
	FOUND_MENDER_VERSION = 0
	FOUND_BIOS_VERSION = 0
	COUNT = 0

	for (i = 1; i <= N; i++)
	{
		prev[i] = ""
	}
}
{
	COUNT = COUNT + 1
	if (/^kura.firmware.version/)
	{
		FOUND_MENDER_VERSION = 1
		if (MENDER_VERSION != $2)
		{
			# Update mender version
			$0 = "kura.firmware.version="MENDER_VERSION
		}
	}
	else if (/^kura.bios.version/)
	{
		FOUND_BIOS_VERSION = 1
		if (SW1_VERSION != $2)
		{
			# Update kura bios version
			$0 = "kura.bios.version="SW1_VERSION
		}
	}
	prev[COUNT] = $0
}
END {
	FS=OLD_FS
	for (i = 1; i < N; i++)
	{
		$0 = prev[i]
		if (prev[i] != "")
		{
			if (/^kura/)
			{
				if (FOUND_MENDER_VERSION == 0)
				{
					FOUND_MENDER_VERSION = 1
					printf("kura.firmware.version=%s\n", MENDER_VERSION)
				}
				if (FOUND_BIOS_VERSION == 0)
				{
					FOUND_BIOS_VERSION = 1
					printf("kura.bios.version=%s\n", SW1_VERSION)
				}
			}
			print prev[i]
		}
	}
}' "${KURA_CUSTOM_PROPERTIES_FILE}" > "${KURA_CUSTOM_PROPERTIES_FILE_TMP}"
mv "${KURA_CUSTOM_PROPERTIES_FILE_TMP}" "${KURA_CUSTOM_PROPERTIES_FILE}"

DIR=$(cd "$(dirname "${0}")/.." || exit; pwd)
cd "$DIR" || exit


# set up the configuration area
mkdir -p /tmp/.kura/configuration
cp "${DIR}"/framework/config.ini /tmp/.kura/configuration/

KURA_RUNNING=$(pgrep --full 'java.*kura')

if [ -z "$KURA_RUNNING" ] ; then
    (nohup java -Xms512m -Xmx512m \
        -XX:+HeapDumpOnOutOfMemoryError -XX:HeapDumpPath=/var/log/kura-heapdump.hprof \
        -XX:ErrorFile=/var/log/kura-error.log \
        -XX:+IgnoreUnrecognizedVMOptions \
        --add-modules=java.sql,java.xml,java.xml.bind \
        -Dkura.os.version=raspbian \
        -Dkura.arch=armv7_hf \
        -Dtarget.device=raspberry-pi-2 \
        -Declipse.ignoreApp=true \
        -Dkura.home="${DIR}" \
        -Dkura.configuration=file:"${DIR}"/framework/kura.properties \
        -Dkura.custom.configuration=file:"${DIR}"/user/kura_custom.properties \
        -Dkura.data.dir="${DIR}"/data \
        -Ddpa.configuration="${DIR}"/data/dpa.properties \
        -Dlog4j.configurationFile=file:"${DIR}"/user/log4j.xml \
        -Djava.security.policy="${DIR}"/framework/jdk.dio.policy \
        -Djdk.dio.registry="${DIR}"/framework/jdk.dio.properties \
        -Djdk.tls.trustNameService=true \
        -Dosgi.console=5002 \
        -Declipse.consoleLog=true \
        -jar "${DIR}"/plugins/org.eclipse.equinox.launcher_1.4.0.v20161219-1356.jar \
	-configuration /tmp/.kura/configuration) &

    #Save the PID
    KURA_PID=$!
    echo "Kura Started (pid=$KURA_PID) ..." >> /var/log/kura-console.log
    echo $KURA_PID > /run/kura.pid
else
    echo "Failed to start Kura. It is already running ..." >> /var/log/kura-console.log
fi
