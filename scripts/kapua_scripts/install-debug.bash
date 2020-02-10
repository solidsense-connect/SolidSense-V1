#!/bin/bash
mv /usr/bin/wm-gw /usr/bin/wm-gw-test
mv wm-gw-debug /usr/bin/wm-gw
chmod +x /usr/bin/wm-gw
echo "Files modified - retasrting service"
systemctl restart wirepasTransport1
echo "service restarted"
systemctl status wirepasTransport1