package com.solidsense.kura;

import java.io.BufferedReader;
import java.io.File;
import java.io.FileReader;
import java.io.IOException;
import java.lang.ProcessBuilder.Redirect;
import java.math.BigInteger;
import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.HashMap;
import java.util.Map;

import org.eclipse.kura.KuraErrorCode;
import org.eclipse.kura.KuraException;
import org.eclipse.kura.configuration.ComponentConfiguration;
import org.eclipse.kura.configuration.SelfConfiguringComponent;
import org.eclipse.kura.core.configuration.ComponentConfigurationImpl;
import org.eclipse.kura.core.configuration.metatype.ObjectFactory;
import org.eclipse.kura.core.configuration.metatype.Tad;
import org.eclipse.kura.core.configuration.metatype.Ticon;
import org.eclipse.kura.core.configuration.metatype.Tocd;
import org.eclipse.kura.core.configuration.metatype.Toption;
import org.eclipse.kura.core.configuration.metatype.Tscalar;
import org.osgi.service.component.ComponentContext;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class WirepasStatusService implements SelfConfiguringComponent {

    private static final Logger s_logger = LoggerFactory.getLogger(WirepasStatusService.class);
    private static final String APP_ID = "com.solidsense.kura.WirepasStatusService";

    private static final String TRANSPORT_A = "wirepasTransport1.service";
    private static final String TRANSPORT_B = "wirepasTransport2.service";
    private static final String MICROSERVICE = "wirepasMicro.service";

    private static final String PATH_BASE = "/data/solidsense/wirepas/";

    private static final String OUTPUT_FILE = "systemctl_status.log";

    private ComponentConfigurationImpl cachedConfiguration;
    private long cachedConfigurationTimestamp;

    private boolean firstConfigurationDone;

    /* ************************************************************************************************************** */

    @Override
    public ComponentConfiguration getConfiguration() throws KuraException {
        s_logger.info("getConfiguration() " + APP_ID);

        try {
            final long configurationAge = System.currentTimeMillis() - cachedConfigurationTimestamp;
            if ((cachedConfiguration == null) || (configurationAge > 5000)) {
                createConfiguration();
            }

            return cachedConfiguration;

        } catch (Exception e) {
            throw new KuraException(KuraErrorCode.INTERNAL_ERROR, e);
        }
    }

    /* ************************************************************************************************************** */

    private void createConfiguration() throws Exception {
        s_logger.info("createConfiguration() " + APP_ID);

        final ObjectFactory objectFactory = new ObjectFactory();
        final Tocd tocd = objectFactory.createTocd();
        final Map<String, Object> props = new HashMap<>();
        props.put("kura.service.pid", APP_ID); // force it

        tocd.setName("Wirepas Data Status");
        tocd.setId(APP_ID);
        tocd.setDescription("Status of the Wirepas MQTT transport modules");

        Ticon tic = objectFactory.createTicon();
        tic.setResource("OSGI-INF/icon.png");
        tic.setSize(new BigInteger("32", 10));
        tocd.setIcon(tic);

        /* create actions selector */
        Tad tad = objectFactory.createTad();
        tad.setId("select.action");
        tad.setName("");
        tad.setType(Tscalar.STRING);
        tad.setCardinality(0);
        tad.setRequired(false);

        Toption toption = objectFactory.createToption();
        toption.setLabel("Select an action");
        toption.setValue("none");
        tad.setOption(toption);

        toption = objectFactory.createToption();
        toption.setLabel("Refresh values");
        toption.setValue("read");
        tad.setOption(toption);

        tocd.addAD(tad);
        props.put("select.action", "none");

        /* ********************** */
        tad = objectFactory.createTad();
        tad.setId("select.status_ts");
        tad.setName("");
        tad.setType(Tscalar.STRING);
        tad.setCardinality(0);
        tad.setRequired(false);
        tad.setMax("");
        tad.setMin("");
        tocd.addAD(tad);
        props.put("select.status_ts", new SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ssXXX").format(new Date()));

        /* ********************** */
        addTransportItems(TRANSPORT_A, "Main MQTT transport", objectFactory, tocd, props);
        addTransportItems(TRANSPORT_B, "Optional MQTT transport", objectFactory, tocd, props);

        /* ********************** */
        cachedConfiguration = new ComponentConfigurationImpl(APP_ID, tocd, props);
        cachedConfigurationTimestamp = System.currentTimeMillis();
    }

    private void addTransportItems(String serviceName, String transportName, ObjectFactory objectFactory, Tocd tocd,
            Map<String, Object> props) {

        Tad tad;

        /* ********************** */
        tad = objectFactory.createTad();
        tad.setId(serviceName + ".status");
        tad.setName("Status of " + transportName);
        tad.setType(Tscalar.STRING);
        tad.setCardinality(0);
        tad.setRequired(false);
        tad.setMax("");
        tad.setMin("");
        tad.setDescription("Status provided by systemD|TextArea");
        tocd.addAD(tad);
        props.put(serviceName + ".status", getServiceStatus(serviceName));

    }

    /* ************************************************************************************************************** */
    protected void activate(ComponentContext componentContext) {
        s_logger.info("Bundle " + APP_ID + " has started!");
        firstConfigurationDone = false;
    }

    protected void activate(ComponentContext componentContext, Map<String, Object> properties) {
        s_logger.info("Bundle " + APP_ID + " has started with config!");
        firstConfigurationDone = false;
    }

    protected void deactivate(ComponentContext componentContext) {
        s_logger.info("Bundle " + APP_ID + " has stopped!");
    }

    /* ************************************************************************************************************** */

    public void updated(Map<String, Object> properties) {
        try {
            s_logger.info("Bundle " + APP_ID + " updated!");

            // update
            createConfiguration();

        } catch (Exception e) {
            s_logger.error(e.toString());
        }
    }

    /* ************************************************************************************************************** */

    private String getServiceStatus(String service) {
        final StringBuilder builder = new StringBuilder();

        /* call systemD */
        executeSystemCtl("status", service);

        /* parse the output */
        try (BufferedReader reader = new BufferedReader(new FileReader(PATH_BASE + OUTPUT_FILE))) {
            String line = reader.readLine(); // drop first line

            line = reader.readLine();
            while (line != null) {
                if (line.startsWith(" ")) {
                    if (line.startsWith("   Active") || line.startsWith("   Memory")) {
                        builder.append(line).append("\n");
                    }
                } else {
                    builder.append(line).append("\n");
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

        File log = new File(PATH_BASE + OUTPUT_FILE);
        log.setLastModified(System.currentTimeMillis());

        pb.redirectErrorStream(true);
        pb.redirectOutput(Redirect.to(log));

        try {
            Process p = pb.start();
            p.waitFor();
            s_logger.info("execute: done");
        } catch (Exception e) {
            s_logger.error(e.toString());
        }

    }

}
