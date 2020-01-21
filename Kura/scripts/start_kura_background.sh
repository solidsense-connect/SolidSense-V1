#!/bin/sh

# Kura should be installed to the /opt/eclipse directory.
export PATH=/bin:/usr/bin:/sbin:/usr/sbin:/usr/local/bin:/opt/jvm/bin:/usr/java/bin:$PATH
export MALLOC_ARENA_MAX=1

# Run the SolidSense provisionning script.
if [ ! -f /opt/eclipse/kura/user/snapshots/snapshot_0.xml ] ; then
    cd "/opt/SolidSense/provisioning" || exit
    python3 /opt/SolidSense/provisioning/SolidSenseProvisionning.py | logger --tag "provisioning" 2>&1
fi

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
