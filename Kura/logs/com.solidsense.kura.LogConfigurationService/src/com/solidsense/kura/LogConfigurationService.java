package com.solidsense.kura;

import java.io.InputStreamReader;
import java.util.ArrayList;
import java.util.Date;
import java.util.HashMap;
import java.util.Map;
import java.util.concurrent.Executors;
import java.util.concurrent.ScheduledExecutorService;
import java.util.concurrent.ScheduledFuture;
import java.util.concurrent.TimeUnit;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

import org.eclipse.kura.cloudconnection.message.KuraMessage;
import org.eclipse.kura.cloudconnection.publisher.CloudPublisher;
import org.eclipse.kura.configuration.ConfigurableComponent;
import org.eclipse.kura.message.KuraPayload;
import org.osgi.service.component.ComponentContext;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class LogConfigurationService implements ConfigurableComponent {

    private static final Logger s_logger = LoggerFactory.getLogger(LogConfigurationService.class);
    private static final String APP_ID = "com.solidsense.kura.LogConfigurationService";

    private volatile CloudPublisher cloudPublisher;

    private static final int NB_STREAM = 2;
    private static final String[] STREAMS = { "stream1", "stream2" };
    private final LogWorker[] workers = new LogWorker[NB_STREAM];

    private static final ThreadGroup threadGroup = new ThreadGroup("Log-Threads");
    private static final String THREAD_PREFIX = "Log-";

    private final ScheduledExecutorService timeoutExecutor = Executors.newSingleThreadScheduledExecutor();

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

        for (int i = 0; i < NB_STREAM; i++) {
            if (workers[i] != null) {
                workers[i].stop();
                workers[i] = null;
            }
        }
    }

    /* ************************************************************************************************************** */

    public void setCloudPublisher(CloudPublisher cloudPublisher) {
        s_logger.info("Bundle " + APP_ID + " has a publisher " + cloudPublisher.toString());
        this.cloudPublisher = cloudPublisher;
    }

    public void unsetCloudPublisher(CloudPublisher cloudPublisher) {
        s_logger.info("Bundle " + APP_ID + " has no publisher");
        this.cloudPublisher = null;
    }

    /* ************************************************************************************************************** */

    public void updated(Map<String, Object> properties) {
        s_logger.info("Bundle " + APP_ID + " updated!");

        /* parse properties */
        if (properties != null && !properties.isEmpty()) {
            for (int i = 0; i < NB_STREAM; i++) {
                updateConf(properties, i);
            }
        }
    }

    private void updateConf(Map<String, Object> properties, int streamIdx) {

        final String streamName = STREAMS[streamIdx];

        Boolean enabled = (Boolean) properties.get(streamName + ".enabled");
        String name = (String) properties.get(streamName + ".name");
        String cmd = (String) properties.get(streamName + ".cmd");
        Integer timeout = (Integer) properties.get(streamName + ".timeout");

        if (enabled) {
            final LogWorker worker = new LogWorker(name, cmd, timeout);
            s_logger.info("updated stream " + streamIdx + " " + worker.toString());

            /* detect config change */
            if ((timeout != 0) || !worker.equals(workers[streamIdx])) {
                if (workers[streamIdx] != null) {
                    workers[streamIdx].stop();
                }

                workers[streamIdx] = worker;
                worker.start();
            }

        } else if (workers[streamIdx] != null) {
            workers[streamIdx].stop();
            workers[streamIdx] = null;
        }

    }

    /* ************************************************** */

    private class LogWorker implements Runnable {

        private String name;
        private final String cmd;
        private final int timeout;

        private final ArrayList<String> cmdList = new ArrayList<>();

        private volatile boolean running;

        /* access protected by synchronized(this) */
        private Thread runner;
        private Process runnerProcess;
        private ScheduledFuture<?> timeoutHandle;

        private static final String DOUBLEQUOTE_TOKEN = "'²";

        public LogWorker(String name, String cmd, int timeout) {
            this.name = name.replace(" ", "_");
            this.cmd = cmd;
            this.timeout = timeout;

            // replace inner double quotes to simplify pattern matching, and restore them after
            Matcher m = Pattern.compile("([^\"]\\S*|\".+?\")\\s*").matcher(cmd.replace("\\\"", DOUBLEQUOTE_TOKEN));
            while (m.find())
                cmdList.add(m.group(1).replace("\"", "").replace(DOUBLEQUOTE_TOKEN, "\""));
        }

        public synchronized void start() {
            s_logger.info("Logworker start : " + name);
            running = true;

            runner = new Thread(threadGroup, this, THREAD_PREFIX + name);
            runner.start();

            if (timeout != 0) {
                final Runnable timeoutJob = new Runnable() {

                    @Override
                    public void run() {
                        publish("stream timeout");
                        s_logger.info("Logworker timeout : " + name);
                        stop();
                    }
                };
                timeoutHandle = timeoutExecutor.schedule(timeoutJob, timeout, TimeUnit.MINUTES);

            }
        }

        public synchronized void stop() {
            if (running) {
                s_logger.info("Logworker stop : " + name);
                running = false;

                if (timeoutHandle != null) {
                    timeoutHandle.cancel(false);
                    timeoutHandle = null;
                }

                try {
                    try {
                        runnerProcess.exitValue(); // will throw exception if process is running
                    } catch (IllegalThreadStateException e) {
                        s_logger.info("Logworker destroy process : " + name);
                        runnerProcess.destroy();
                    }
                } catch (Exception e) {
                }

                runnerProcess = null;
                runner = null;
            }
        }

        @Override
        public void run() {
            InputStreamReader inReader = null;
            char[] buffer = new char[1024];

            try {
                synchronized (this) {
                    /* start process - start/stop race is not an issue in this use case */

                    final ProcessBuilder pb = new ProcessBuilder(cmdList);
                    pb.redirectErrorStream(true);

                    runnerProcess = pb.start();
                    inReader = new InputStreamReader(runnerProcess.getInputStream());
                }

                while (running) {
                    int length = inReader.read(buffer, 0, 1024); // blocking call

                    if (running) {
                        if (length == -1) {
                            publish("end of stream");
                            return;
                        }

                        String msg = new String(buffer, 0, length);
                        publish(msg);
                    }
                }

            } catch (Exception e) {
                e.printStackTrace();
                publish(e.getMessage());
            }
        }

        private void publish(String msg) {
            KuraPayload payload = new KuraPayload();
            payload.setTimestamp(new Date());
            payload.addMetric("message", msg);

            HashMap<String, Object> msgProps = new HashMap<>();
            msgProps.put("name", name);

            KuraMessage message = new KuraMessage(payload, msgProps);

            try {
                CloudPublisher publisher = cloudPublisher; // latch volatile variable
                if (publisher != null) {
                    publisher.publish(message);
                }
            } catch (Exception e) {
                s_logger.error("Cannot publish message: {}", message, e);
            }

        }

        @Override
        public String toString() {
            return "LogWorker [name=" + name + ", cmd=" + cmd + ", timeout=" + timeout + ", cmdList=" + cmdList + "]";
        }

        @Override
        public int hashCode() {
            final int prime = 31;
            int result = 1;
            result = prime * result + ((cmd == null) ? 0 : cmd.hashCode());
            result = prime * result + ((name == null) ? 0 : name.hashCode());
            result = prime * result + timeout;
            return result;
        }

        @Override
        public boolean equals(Object obj) {
            if (this == obj)
                return true;
            if (obj == null)
                return false;
            if (getClass() != obj.getClass())
                return false;
            LogWorker other = (LogWorker) obj;

            if (cmd == null) {
                if (other.cmd != null)
                    return false;
            } else if (!cmd.equals(other.cmd))
                return false;
            if (name == null) {
                if (other.name != null)
                    return false;
            } else if (!name.equals(other.name))
                return false;
            if (timeout != other.timeout)
                return false;
            return true;
        }

    } /* private class LogWorker */
}
