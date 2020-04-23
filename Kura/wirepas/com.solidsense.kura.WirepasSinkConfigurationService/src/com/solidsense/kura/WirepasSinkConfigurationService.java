package com.solidsense.kura;

import java.io.File;
import java.io.FileWriter;
import java.io.IOException;
import java.lang.ProcessBuilder.Redirect;
import java.util.Map;

import org.eclipse.kura.configuration.ConfigurableComponent;
import org.osgi.service.component.ComponentContext;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class WirepasSinkConfigurationService implements ConfigurableComponent {

    private static final Logger s_logger = LoggerFactory.getLogger(WirepasSinkConfigurationService.class);
    private static final String APP_ID = "com.solidsense.kura.WirepasSinkConfigurationService";

    private static final String SERVICE_NAME = "wirepasSinkConfig.service";
    private static final String PATH_BASE = "/data/solidsense/wirepas/";

    private boolean ignoreUpdate;

    /* ************************************************************************************************************** */

    protected void activate(ComponentContext componentContext, Map<String, Object> properties) {
        s_logger.info("Bundle " + APP_ID + " has started with config!");

        if (properties != null) {
            final String sinkName = (String) properties.get("sinkName");
            ignoreUpdate = (sinkName != null);

            if (!ignoreUpdate) {
                s_logger.info("Bundle " + APP_ID + " ready!");
            }
        }

    }

    protected void deactivate(ComponentContext componentContext) {
        s_logger.info("Bundle " + APP_ID + " has stopped!");
    }

    /* ************************************************************************************************************** */

    public void updated(Map<String, Object> properties) {
        final String sinkName = (String) properties.get("sinkName");

        if (ignoreUpdate || (sinkName == null)) {
            ignoreUpdate = false;             // ignore automatic seed at startup, because we are not really a
                                              // ConfigurableComponent...

            s_logger.info("Bundle " + APP_ID + " already updated!");
            return;
        }

        s_logger.info("Bundle " + APP_ID + " updated!");

        /* parse properties */
        Integer sinkAddress = (Integer) properties.get("sinkAddress");
        Integer networkAddress = (Integer) properties.get("networkAddress");
        Integer networkChannel = (Integer) properties.get("networkChannel");

        try (FileWriter writer = new FileWriter(PATH_BASE + SERVICE_NAME + ".cfg")) {

            writer.write("-s=" + sinkName + "\n");
            writer.write("-n=" + sinkAddress + "\n");
            writer.write("-N=" + networkAddress + "\n");
            writer.write("-c=" + networkChannel + "\n");
            writer.write("-S=true\n");

        } catch (IOException e) {
            e.printStackTrace();
        }

        executeSystemCtl("start", SERVICE_NAME);

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
