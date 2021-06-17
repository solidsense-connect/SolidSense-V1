package com.solidsense.kura;

import java.io.File;
import java.io.FileWriter;
import java.io.IOException;
import java.lang.ProcessBuilder.Redirect;
import java.util.Map;

import org.eclipse.kura.configuration.ConfigurableComponent;
import org.eclipse.kura.system.SystemService;
import org.osgi.service.component.ComponentContext;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class WirepasConfigurationService implements ConfigurableComponent {

    private static final Logger s_logger = LoggerFactory.getLogger(WirepasConfigurationService.class);
    private static final String APP_ID = "com.solidsense.kura.WirepasConfigurationService";

    private static final String TRANSPORT_A = "wirepasTransport1.service";
    private static final String TRANSPORT_B = "wirepasTransport2.service";
    private static final String MICROSERVICE = "wirepasMicro.service";

    private static final String PATH_BASE = "/data/solidsense/wirepas/";

    private SystemService systemService;

    /* ************************************************************************************************************** */

    protected void activate(ComponentContext componentContext) {
        s_logger.info("Bundle " + APP_ID + " has started!");
    }

    protected void activate(ComponentContext componentContext, Map<String, Object> properties) {
        s_logger.info("Bundle " + APP_ID + " has started with config!");
        updated(properties);
    }

    protected void deactivate(ComponentContext componentContext) {
        s_logger.info("Bundle " + APP_ID + " has stopped!");
    }

    /* ************************************************************************************************************** */

    protected void setSystemService(SystemService sms) {
        systemService = sms;
    }

    /* ************************************************************************************************************** */

    public void updated(Map<String, Object> properties) {
        s_logger.info("Bundle " + APP_ID + " updated!");

        /* stop services */
        executeSystemCtl("stop", TRANSPORT_A);
        executeSystemCtl("stop", TRANSPORT_B);
        executeSystemCtl("stop", MICROSERVICE);

        /* parse properties */
        if (properties != null && !properties.isEmpty()) {
            String gatewayID = (String) properties.get("gatewayID");
            String customID = (String) properties.get("customID");
            customID = (customID != null) ? customID.trim() : "";

            String gatewayName = null;
            switch (gatewayID) {
            case "device":
                gatewayName = customID + systemService.getDeviceName();
                break;

            case "custom":
                gatewayName = customID;
                break;
            }

            Boolean enabled = (Boolean) properties.get("transportA.enabled");
            if (enabled) {
                updateConf(properties, "transportA", TRANSPORT_A, gatewayName, true);
            }

            enabled = (Boolean) properties.get("transportB.enabled");
            if (enabled) {
                updateConf(properties, "transportB", TRANSPORT_B, gatewayName, false);
            }

            enabled = (Boolean) properties.get("microService.enabled");
            if (enabled) {
                updateMicroConf(properties);
            }
        }
    }

    /*
     * #
     * # MQTT brocker Settings
     * #
     * mqtt_hostname: <IP or hostname where the MQTT broker is located>
     * mqtt_port: <MQTT port (default: 8883 (secure) or 1883 (local))>
     * mqtt_username: <MQTT user>
     * mqtt_password: <MQTT password>
     * mqtt_force_unsecure: <True to disable TLS secure authentication>
     * mqtt_persist_session: <True to ask broker to buffer session packets>
     * 
     * #
     * # Gateway settings
     * #
     * gateway_id: <the desired gateway id, must be unique for each gateway>
     * gateway_model: <Custom gateway model, can be omitted>
     * gateway_version: <Custom gateway version, can be omitted>
     * 
     * #
     * # Implementation options
     * #
     * full_python: <Set to true to not use the C extension>
     * 
     * #
     * # Filtering Destination Endpoints
     * #
     * ignored_endpoints_filter: <Endpoints to filter out. Ex: [1, 2, 10-12]>
     * whitened_endpoints_filter: <Endpoints to whiten. Ex: [1, 2, 10-12]>
     * 
     */

    private void updateConf(Map<String, Object> properties, String prefix, String service, String gatewayName,
            boolean mainTransport) {

        String address = (String) properties.get(prefix + ".address");
        Integer port = (Integer) properties.get(prefix + ".port");
        String user = (String) properties.get(prefix + ".user");
        String pass = (String) properties.get(prefix + ".passwd");
        Boolean secure = (Boolean) properties.get(prefix + ".secured");
        Boolean persist = (Boolean) properties.get(prefix + ".persist");
        String userOptions = (String) properties.get(prefix + ".options");

        Integer maxPackets = (mainTransport) ? (Integer) properties.get(prefix + ".maxpacket") : 0;
        Integer maxDelay = (mainTransport) ? (Integer) properties.get(prefix + ".maxdelay") : 0;

        try (FileWriter writer = new FileWriter(PATH_BASE + service + ".cfg")) {

            writer.write("# MQTT brocker Settings\n");
            writer.write("mqtt_hostname: " + address + "\n");
            writer.write("mqtt_port: " + port + "\n");
            writer.write("mqtt_username: " + user + "\n");
            writer.write("mqtt_password: " + pass + "\n");
            writer.write("mqtt_force_unsecure: " + (secure ? "False" : "True") + "\n");
            writer.write("mqtt_persist_session: " + (persist ? "True" : "False") + "\n");
            writer.write("\n");

            writer.write("# Gateway settings\n");
            if (gatewayName != null) {
                writer.write("gateway_id: " + gatewayName + "\n");
            }
            if (mainTransport) {
                writer.write("status_led: 1\n");
            }
            writer.write("status_file: " + PATH_BASE + service + ".status" + "\n");
            writer.write("\n");

            writer.write("# Implementation options\n");
            writer.write("full_python: False\n");
            writer.write("\n");

            writer.write("# Black-Hole detection options\n");
            writer.write("buffering_max_buffered_packets: " + maxPackets + "\n");
            writer.write("buffering_max_delay_without_publish: " + maxDelay + "\n");
            writer.write("\n");

            writer.write("# User options\n");
            writer.write(userOptions);
            writer.write("\n\n");
            writer.write("# End\n");

        } catch (Exception e) {
            e.printStackTrace();
        }

        /* start service */
        executeSystemCtl("start", service);
    }

    private void updateMicroConf(Map<String, Object> properties) {

        Boolean global = (Boolean) properties.get("microService.global");

        try (FileWriter writer = new FileWriter(PATH_BASE + MICROSERVICE + ".cfg")) {

            writer.write("# Local Microservice Settings\n");
            writer.write("# We use default settings for most of the parameters\n");
            writer.write("host: " + (global ? "'[::]'" : "127.0.0.1") + "\n");
            writer.write("\n");

        } catch (IOException e) {
            e.printStackTrace();
        }

        /* start service */
        executeSystemCtl("start", MICROSERVICE);
    }

    private void executeSystemCtl(String command, String service) {
        s_logger.info("execute: systemctl " + command + " " + service);
        final ProcessBuilder pb = new ProcessBuilder("systemctl", command, service);

        File log = new File(PATH_BASE + "systemctl.log");
        log.setLastModified(System.currentTimeMillis());

        pb.redirectErrorStream(true);
        pb.redirectOutput(Redirect.appendTo(log));

        try {
            Process p = pb.start();
            p.waitFor();
            s_logger.info("execute: done");
        } catch (Exception e) {
            e.printStackTrace();
        }

    }
}
