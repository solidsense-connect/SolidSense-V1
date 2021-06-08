package com.solidsense.kura;

import java.io.BufferedReader;
import java.io.File;
import java.io.FileReader;
import java.io.FileWriter;
import java.io.IOException;
import java.lang.ProcessBuilder.Redirect;
import java.math.BigInteger;
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

public class WirepasSinkConfigurationService implements SelfConfiguringComponent {

    private static final Logger s_logger = LoggerFactory.getLogger(WirepasSinkConfigurationService.class);
    private static final String APP_ID = "com.solidsense.kura.WirepasSinkConfigurationService";

    private static final String SERVICE_NAME = "wirepasSinkConfig.service";
    private static final String PATH_BASE = "/data/solidsense/wirepas/";

    private static final String CONFIG_SUFFIX = ".cfg";
    private static final String OUTPUT_SUFFIX = ".log";

    private static final String KEY_SET_MSG_YES = "YES";
    private static final String KEY_SET_MSG_NO = "";

    private static final String ACTION_WRITE_ALL = "writeAll";

    private ComponentConfigurationImpl cachedConfiguration;

    private final HashMap<String, String> lastConfigurationMessage = new HashMap<String, String>();
    private static final String CONFIGURATION_OK = "GatewayResultCode.GW_RES_OK";

    private boolean firstConfigurationDone;

    /* ************************************************************************************************************** */

    @Override
    public ComponentConfiguration getConfiguration() throws KuraException {
        s_logger.info("getConfiguration() " + APP_ID);

        try {
            if (cachedConfiguration == null) {
                createConfiguration();

                /*
                 * Exception e = new RuntimeException();
                 * StackTraceElement[] stackTrace = e.getStackTrace();
                 * for (StackTraceElement se : stackTrace) {
                 * s_logger.info(se.toString());
                 * }
                 */
            }

            return cachedConfiguration;

        } catch (Exception e) {
            throw new KuraException(KuraErrorCode.INTERNAL_ERROR, e);
        }
    }

    private void createConfiguration() throws Exception {
        s_logger.info("createConfiguration() " + APP_ID);

        final ObjectFactory objectFactory = new ObjectFactory();
        final Tocd tocd = objectFactory.createTocd();
        final Map<String, Object> props = new HashMap<>();
        props.put("kura.service.pid", APP_ID); // force it

        tocd.setName("Wirepas Sink Configuration");
        tocd.setId(APP_ID);
        tocd.setDescription("Configuration of the sinks available in this gateway");

        Ticon tic = objectFactory.createTicon();
        tic.setResource("OSGI-INF/icon.png");
        tic.setSize(new BigInteger("32", 10));
        tocd.setIcon(tic);

        final HashMap<String, HashMap<String, String>> sinksConfig = executeCmdList();

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

        toption = objectFactory.createToption();
        toption.setLabel("Configure all the sinks");
        toption.setValue("writeAll");
        tad.setOption(toption);

        for (String id : sinksConfig.keySet()) {
            toption = objectFactory.createToption();
            toption.setLabel("Configure " + id);
            toption.setValue(id);
            tad.setOption(toption);
        }

        tocd.addAD(tad);
        props.put("select.action", "none");

        if (sinksConfig.isEmpty()) {
            tad = objectFactory.createTad();
            tad.setId("empty.title");
            tad.setName("");
            tad.setType(Tscalar.STRING);
            tad.setCardinality(0);
            tad.setRequired(false);
            tad.setMax("");
            tad.setMin("");
            tocd.addAD(tad);
            props.put("empty.title", "No sink detected");

        } else {
            for (int i = 1; i < 10; i++) { // sort sink-id
                final HashMap<String, String> cfg = sinksConfig.get("sink" + i);
                if (cfg != null) {
                    updateItems(objectFactory, tocd, props, cfg);
                }
            }
        }

        cachedConfiguration = new ComponentConfigurationImpl(APP_ID, tocd, props);
    }

    private void updateItems(ObjectFactory objectFactory, Tocd tocd, Map<String, Object> props,
            HashMap<String, String> cfg) {

        final String sinkName = cfg.get("[sink_id]");
        final String lastResult = lastConfigurationMessage.get(sinkName);
        Tad tad;
        String paramString;

        /* ********************** */
        tad = objectFactory.createTad();
        tad.setId(sinkName + ".title");
        tad.setName("");
        tad.setType(Tscalar.STRING);
        tad.setCardinality(0);
        tad.setRequired(false);
        tad.setMax("");
        tad.setMin("");
        tocd.addAD(tad);

        String title = "Configuration of " + sinkName;
        if ((lastResult != null) && (!lastResult.equals(CONFIGURATION_OK))) {
            title += "  [ Configuration error: " + lastResult + " ]";
        }
        props.put(sinkName + ".title", title);

        /* ********************** */
        tad = objectFactory.createTad();
        tad.setId(sinkName + ".started");
        tad.setName(sinkName + " - running");
        tad.setType(Tscalar.BOOLEAN);
        tad.setCardinality(0);
        tad.setRequired(false);
        // tad.setDefault("false");
        tocd.addAD(tad);
        paramString = cfg.get("[started]");
        props.put(sinkName + ".started", "True".equals(paramString));

        /* ********************** */
        tad = objectFactory.createTad();
        tad.setId(sinkName + ".stackVersion");
        tad.setName(sinkName + " - stack version");
        tad.setType(Tscalar.STRING);
        tad.setCardinality(0);
        tad.setRequired(false);
        tad.setMax("");
        tad.setMin("");
        tocd.addAD(tad);

        paramString = cfg.get("[firmware_version]");
        if (paramString == null) {
            paramString = "Unknown";
        } else {
            paramString = paramString.replace(", ", ".").replace("[", "").replace("]", "");
        }
        props.put(sinkName + ".stackVersion", paramString);

        /* ********************** */
        tad = objectFactory.createTad();
        tad.setId(sinkName + ".sinkAddress");
        tad.setName(sinkName + " - address");
        tad.setType(Tscalar.INTEGER);
        tad.setCardinality(0);
        tad.setRequired(false);
        tad.setMin("0");
        tad.setDefault("0");
        tocd.addAD(tad);

        paramString = cfg.get("[node_address]");
        if (paramString != null) {
            props.put(sinkName + ".sinkAddress", Integer.valueOf(paramString));
        }

        /* ********************** */
        tad = objectFactory.createTad();
        tad.setId(sinkName + ".networkAddress");
        tad.setName(sinkName + " - network address");
        tad.setType(Tscalar.INTEGER);
        tad.setCardinality(0);
        tad.setRequired(false);
        tad.setMin("0");
        tad.setDefault("0");
        // tad.setMax("16777214");
        tocd.addAD(tad);

        paramString = cfg.get("[network_address]");
        if (paramString != null) {
            props.put(sinkName + ".networkAddress", Integer.valueOf(paramString));
        }

        /* ********************** */
        tad = objectFactory.createTad();
        tad.setId(sinkName + ".networkChannel");
        tad.setName(sinkName + " - network channel");
        tad.setType(Tscalar.INTEGER);
        tad.setCardinality(0);
        tad.setRequired(false);
        tad.setMax("40");
        tad.setMin("0");
        tad.setDefault("0");
        tocd.addAD(tad);

        paramString = cfg.get("[network_channel]");
        if (paramString != null) {
            props.put(sinkName + ".networkChannel", Integer.valueOf(paramString));
        }

        /* ********************** */
        tad = objectFactory.createTad();
        tad.setId(sinkName + ".auth");
        tad.setName(sinkName + " - authentication key");
        tad.setType(Tscalar.STRING);
        tad.setCardinality(0);
        tad.setRequired(false);
        tocd.addAD(tad);

        tad = objectFactory.createTad();
        tad.setId(sinkName + ".cipher");
        tad.setName(sinkName + " - cipher key");
        tad.setType(Tscalar.STRING);
        tad.setCardinality(0);
        tad.setRequired(false);
        tocd.addAD(tad);

        paramString = cfg.get("[are_keys_set]");
        if ("True".equals(paramString)) {
            paramString = KEY_SET_MSG_YES;
        } else {
            paramString = KEY_SET_MSG_NO;
        }
        props.put(sinkName + ".auth", paramString);
        props.put(sinkName + ".cipher", paramString);
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

    private HashMap<String, Object> filterSinkProperties(Map<String, Object> properties, String sinkId) {
        final HashMap<String, Object> sinkProperties = new HashMap<>();
        final int prefix = sinkId.length() + 1;

        for (Map.Entry<String, Object> entry : properties.entrySet()) {
            String key = entry.getKey();
            if (key.startsWith(sinkId)) {
                sinkProperties.put(key.substring(prefix), entry.getValue());
            }
        }

        return sinkProperties;
    }

    public void updated(Map<String, Object> properties) {
        try {
            if (firstConfigurationDone) {
                s_logger.info("Bundle " + APP_ID + " updated!");
                s_logger.info(properties.toString());
                lastConfigurationMessage.clear();

                final String action = (String) properties.get("select.action");
                if (action.equals(ACTION_WRITE_ALL)) {
                    for (int i = 1; i < 10; i++) { // for all sinks
                        if (properties.get(("sink" + i + ".started")) != null) {
                            executeCmdSet(("sink" + i), filterSinkProperties(properties, ("sink" + i)));
                        }
                    }
                } else if (action.startsWith("sink")) { // sinkID
                    executeCmdSet(action, filterSinkProperties(properties, action));
                }

            } else {
                firstConfigurationDone = true;
                s_logger.info("Bundle " + APP_ID + " first update skipped!");
            }

            // update
            createConfiguration();

        } catch (Exception e) {
            s_logger.error(e.toString());
        }
    }

    /* ************************************************************************************************************** */

    private HashMap<String, HashMap<String, String>> executeCmdList() {
        final HashMap<String, HashMap<String, String>> config = new HashMap<>();

        /* create the list command */
        try (FileWriter writer = new FileWriter(PATH_BASE + SERVICE_NAME + CONFIG_SUFFIX)) {
            writer.write("list");
        } catch (IOException e) {
            e.printStackTrace();
            return config; // return empty result
        }

        /* Erase old output file */
        new File(PATH_BASE + SERVICE_NAME + OUTPUT_SUFFIX).delete();

        /* execute the service */
        executeSystemCtl("start", SERVICE_NAME);

        /* parse the output */
        try (BufferedReader reader = new BufferedReader(new FileReader(PATH_BASE + SERVICE_NAME + OUTPUT_SUFFIX))) {
            String line = reader.readLine();
            while (line != null) {
                /* find start of the sink data */
                if (line.startsWith("============== [")) {
                    final String sinkName = line.replace("============== [", "").replace("] ===============", "");
                    final HashMap<String, String> sinkData = new HashMap<>();

                    line = reader.readLine();
                    /* while not the end of the sink data */
                    while ((line != null) && !line.startsWith("==============")) {
                        if (line.startsWith("[")) {
                            int pos = line.indexOf(":");
                            String attributeName = line.substring(0, pos);
                            String attributeValue = line.substring(pos + 2);

                            sinkData.put(attributeName, attributeValue);
                        }

                        line = reader.readLine();
                    } /* while () */

                    config.put(sinkName, sinkData);
                } /* if (line.startsWith("============== [")) */

                line = reader.readLine();
            } /* while (line != null) */

        } catch (IOException e) {
            s_logger.error(e.toString());
        }

        return config;
    }

    private void executeCmdSet(String sinkId, HashMap<String, Object> sinkProperties) {
        s_logger.info("executeCmdSet: " + sinkProperties.toString());

        final String RESULT_PREFIX = "Configuration done with result = ";
        final int prefix_size = RESULT_PREFIX.length();

        try (FileWriter writer = new FileWriter(PATH_BASE + SERVICE_NAME + CONFIG_SUFFIX)) {

            /* parse properties */
            Integer sinkAddress = (Integer) sinkProperties.get("sinkAddress");
            Integer networkAddress = (Integer) sinkProperties.get("networkAddress");
            Integer networkChannel = (Integer) sinkProperties.get("networkChannel");
            Boolean started = (Boolean) sinkProperties.get("started");
            String authKey = (String) sinkProperties.get("auth");
            String cipherKey = (String) sinkProperties.get("cipher");

            writer.write("set\n");
            writer.write("-s=" + sinkId + "\n");
            writer.write("-n=" + sinkAddress + "\n");
            writer.write("-r=sink csma-ca\n");
            writer.write("-N=" + networkAddress + "\n");
            writer.write("-c=" + networkChannel + "\n");

            if ((authKey.length() == 32) && !authKey.equals(KEY_SET_MSG_YES)) {
                writer.write("-ak=" + authKey + "\n");
            }
            if ((authKey.length() == 32) && !cipherKey.equals(KEY_SET_MSG_YES)) {
                writer.write("-ck=" + cipherKey + "\n");
            }

            writer.write("-S=" + (started ? "1" : "0") + "\n");

        } catch (IOException e) {
            s_logger.error(e.toString());
            return;
        }

        executeSystemCtl("start", SERVICE_NAME);

        /* parse the output */
        try (BufferedReader reader = new BufferedReader(new FileReader(PATH_BASE + SERVICE_NAME + OUTPUT_SUFFIX))) {
            String line = reader.readLine();
            while (line != null) {
                if (line.startsWith(RESULT_PREFIX)) {
                    lastConfigurationMessage.put(sinkId, line.substring(prefix_size));
                    break;
                }

                line = reader.readLine();
            } /* while (line != null) */

        } catch (IOException e) {
            s_logger.error(e.toString());
        }
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
            s_logger.error(e.toString());
        }

    }

}
