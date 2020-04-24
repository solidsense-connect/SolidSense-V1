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

public class SolidsenseMqttService implements ConfigurableComponent {

    private static final Logger s_logger = LoggerFactory.getLogger(SolidsenseMqttService.class);
    private static final String APP_ID = "com.solidsense.kura.SolidsenseMqttService";

    private static final String TRANSPORT = "solidsense_mqtt.service";
    private static final String PATH_BASE = "/data/solidsense/mqtt/";
    
    private static final String FALSE = "False";
    private static final String TRUE  = "True";

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
        executeSystemCtl("stop", TRANSPORT);

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

            Boolean enabled = (Boolean) properties.get("transport.enabled");
            if (enabled) {
                updateConf(properties, gatewayName);
            }
        }
    }

    /*
     * #
     * # MQTT broker Settings
     * #
     * mqtt_hostname: <IP or hostname where the MQTT broker is located>
     * mqtt_port: <MQTT port (default: 8883)>
     * mqtt_username: <MQTT user>
     * mqtt_password: <MQTT password>
     * mqtt_force_unsecure: <True to disable TLS secure authentication>
     * 
     * #
     * # Gateway settings
     * #
     * gateway_id: <the desired gateway id, must be unique for each gateway>
     * gateway_model: <Custom gateway model, can be omitted>
     * gateway_version: <Custom gateway version, can be omitted>
     * 
     * #
     * # BLE settings
     * #
     * ble: <True to activate>
     * ble_interface : hic0,hci2
     * autostart: <True to activate>
     * 
     * #
     * # MS settings
     * #
     * modem_gps: <True to activate>
     * obd_device: <True to activate>
     */

    private void updateConf(Map<String, Object> properties, String gatewayName) {
    	
        String address = (String) properties.get("transport.address");
        Integer port = (Integer) properties.get("transport.port");
        String user = (String) properties.get("transport.user");
        String pass = (String) properties.get("transport.passwd");
        Boolean secure = (Boolean) properties.get("transport.secured");
        
        Boolean ble = (Boolean) properties.get("transport.ble");
        Boolean hci0 = (Boolean) properties.get("transport.hci0");
        Boolean hci1 = (Boolean) properties.get("transport.hci1");
        Boolean hci2 = (Boolean) properties.get("transport.hci2");
        Boolean autostart = (Boolean) properties.get("transport.autostart");
        
        Boolean modemgps = (Boolean) properties.get("transport.modemgps");
        Boolean obd = (Boolean) properties.get("transport.obd");
        String  obddongle = (String) properties.get("transport.obddongle");
        
        String  userOptions = (String) properties.get("transport.options");


        try (FileWriter writer = new FileWriter(PATH_BASE + TRANSPORT + ".cfg")) {

            writer.write("# MQTT brocker Settings\n");
            writer.write("mqtt_hostname: " + address + "\n");
            writer.write("mqtt_port: " + port + "\n");
            writer.write("mqtt_username: " + user + "\n");
            writer.write("mqtt_password: " + pass + "\n");
            writer.write("mqtt_force_unsecure: " + (secure ? FALSE : TRUE) + "\n");
            writer.write("\n");

            writer.write("# Gateway settings\n");
            if (gatewayName != null) {
                writer.write("gateway_id: " + gatewayName + "\n");
            }
            writer.write("\n");

            writer.write("# BLE settings\n");
            ble = ble && (hci0 || hci1 || hci2); // disabled if no interface enabled
            writer.write("ble: " + (ble ? TRUE : FALSE) + "\n");
            if (ble) {
	            String bleInterface = "";
	            if (hci0) { bleInterface += ",hci0"; }
	            if (hci1) { bleInterface += ",hci1"; }
	            if (hci2) { bleInterface += ",hci2"; }
	            writer.write("ble_interface: " + bleInterface.substring(1) + "\n");
            }
            writer.write("autostart: " + (autostart ? TRUE : FALSE) + "\n");
            writer.write("\n");

            writer.write("# MS settings\n");
            writer.write("modem_gps: " + (modemgps ? TRUE : FALSE) + "\n");
            if (obd) {
            	writer.write("obd_device: " + obddongle + "\n");
            }
            writer.write("\n");
            
            writer.write("# User options\n");
            writer.write(userOptions);
            writer.write("\n\n");
            writer.write("# End\n");

        } catch (IOException e) {
            e.printStackTrace();
        }

        /* start service */
        executeSystemCtl("start", TRANSPORT);
    }

    private void executeSystemCtl(String command, String service) {
        final ProcessBuilder pb = new ProcessBuilder("systemctl", command, service);

        File log = new File(PATH_BASE + "systemctl.log");
        pb.redirectErrorStream(true);
        pb.redirectOutput(Redirect.appendTo(log));

        try {
            Process p = pb.start();
            p.waitFor();
        } catch (Exception e) {
            e.printStackTrace();
        }
    }
}
