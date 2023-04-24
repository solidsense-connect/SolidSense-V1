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

public class OpenVPNConfigurationService implements ConfigurableComponent {

    private static final Logger s_logger = LoggerFactory.getLogger(OpenVPNConfigurationService.class);
    private static final String APP_ID = "com.solidsense.kura.OpenVPNConfigurationService";

    private static final String OPENVPN = "openvpn@client.service";

    private static final String PATH_BASE = "/data/openvpn/";

    private SystemService systemService;

    /* ************************************************************************************************************** */

    protected void activate(ComponentContext componentContext) {
        s_logger.info("Bundle " + APP_ID + " has started!");
    }

    protected void activate(ComponentContext componentContext, Map<String, Object> properties) {
        s_logger.info("Bundle " + APP_ID + " has started with config!");
        start(properties);
    }

    protected void deactivate(ComponentContext componentContext) {
        s_logger.info("Bundle " + APP_ID + " has stopped!");
        stop();
    }

    /* ************************************************************************************************************** */

    protected void setSystemService(SystemService sms) {
        systemService = sms;
    }

    /* ************************************************************************************************************** */

    public void start(Map<String, Object> properties) {
        executeSystemCtl("start", OPENVPN);
        getBundle();
        getConfig();
        getStatus();
    }

    public void stop() {
        executeSystemCtl("stop", OPENVPN);
    }

    private String getBundle() {
        String content;
        Path path = Paths.get("/data/Sodira/certs/bundle.crt");

        try {
            byte[] encoded = Files.readAllBytes(path);
            content = new String(encoded, StandardCharsets.UTF_8);
            properties.replace("config", content);
        }
        catch (IOException e) {
            s_logger.info(e.toString());
        }
    }

    private String getPrivateKey() {
        s_logger.info("Device certificate: Print Private Key HERE");
    }

    private String getConfig() {
        String content;
        Path path = Paths.get(PATH_BASE + "client.conf");
 
        try {
            byte[] encoded = Files.readAllBytes(path);
            content = new String(encoded, StandardCharsets.UTF_8);
            properties.replace("config", content);
        }
        catch (IOException e) {
            s_logger.info(e.toString());
        }
    }

    private String getStatus() {
        final StringBuilder builder = new StringBuilder();

        /* call systemD */
        executeSystemCtl("status", service);

        /* parse the output */
        try (BufferedReader reader = new BufferedReader(new FileReader(PATH_BASE + "systemctl.log"))) {
            String line = reader.readLine(); // drop first line

            line = reader.readLine();
            while (line != null) {
                if (line.startsWith("   Active")) {
                    properties.replace("status", line);
                }

                line = reader.readLine();
            } /* while (line != null) */

        } catch (IOException e) {
            s_logger.error(e.toString());
        }

        return builder.toString();
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

    /* ************************************************************************************************************** */
}
