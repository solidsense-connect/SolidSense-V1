# SolidSense-V1
Version V1 of the gateway based on CIP

# Provisioning

Key feature added in V0.95 allowing a flexible provisioning of the gateway.
This is done via several Yaml files that are processed upon initial boot by the provisioning process script.

The structure, keywords and parameter values for the Yaml files are not developed in this page.

## Principle

The provisioning process interprets the configuration Yaml files and generates all configuration files needed by the system. Then it enable and possibly start all systemd services that needs to be enabled and/or started.
The provisioning process is run automatically a boot whenever the Kura snapshop_0.xml is not present.

The following files are generated:
1. /opt/eclipse/kura/user/kura_custom.properties
2. /opt/eclipse/kura/user/kuranet.conf
3. /opt/eclipse/kura/data/dpa.properties
4. /opt/eclipse/kura/user/snapshots/snapshot_0.xml
5. /etc/hostapd-wlan0.conf

Other service specific files can be generated in /data/solidsense

All Kura properties (from all services) can be manipulated (modified/added). All service specific parameters can be manipulated as well.


## Factory configuration (read-only)

The factory configuration includes 2 files that shall be located in /opt/SolidSense/config
1. SolidSense-conf-base.yml	=> Generic standard configuration
2. SolidSense-HW-configurations => Definition of HW configuration description

The provisioning process also make use of files located in /opt/SolidSense/template

### Default configuration

Network:
Ethernet (eth0): WAN DHCP client
WiFi (wlan0) : LAN Access Point (WPA2) DHCP Server SSID=Serial Number
Celullar (ppp0) : Not configured

Services:
MQTT Client for Kura: enabled
modem_gps: enabled if the modem is present


## Customer specific configuration

The customer specific configuration Yaml file is /data/solidsense/config/SolidSense-conf-custom.yml. That file is optional, and if the provisioning does not find it is applies only the Factory configuration. In that case optional interfaces (Bluetooth, Wirepas) must be configured via Kura

### Custom reference configuration files

There are 3 reference/sample files in the custom directory. They must be renamed 'SolidSense-conf-custom.yml' and copied in the /data/solidsense:config directory to be effective.


Sample configuration file for reference for a more diverse configuration:

- adding ppp0 as WAN interface
- adding Wirepas services
- adding the Bluetooth service
- Configuring default values including WiFi keys, Kura web credentials...

Additional files and tips to be published on the developer Wiki

### Applying a custom automatic configuration

The process to apply the custom configuration (outside factory installation) is the following:
1- Copy the file with configuration (Provisioning YAML file) into /data/solidsense:config/SolidSense-conf-custom.yml
2- Wipe out overlay file system
3- reboot

After the complete reboot the gateway is ready nwith the configuration, so no need to have interactive entries.


# RPMB content

The RPMB includes configuration parameters and is exclusively written in factory during the production process.
This is an ASCII string, with a general syntax <KEYWORD>=<VALUE> separated by comma.

**The RPMB content is processed by the provisioning system to automitically populate all configuration files**

## Keywords
1. PART: Full partnumber including product code and revison (ex: SRG0002.01)
2. SERIAL: Serial number of the product (ex: BS18170012)
3. PRODUCT: Product code == hardware configuration (ex: SRG0002)
4. NORDIC1_TYPE: Type of the sink1 (NINAB1/NINAB3)
5. NORDIC2_TYPE: Type of the sink2
If a specific firmware is flashed in the sink(s) then the 2 follwing fields are added
6. STACK1_TYPE: type of firmware flashed
7. STACK2_TYPE:         
	UB: Ublox connectivity SW   
        HC: HCI Bluetooth stack
	WP: Wirepas stack
	
8. STACK1_VERSION: Version string
9. STACK2_VERSION:

## Example

Gateway indoor with unflashed Nordic
PART=SRG0002.01,SERIAL=BS181300065,PRODUCT=SRG0002,NORDIC1_TYPE=NINAB1,NORDIC2_TYPE=NINAB1

Gateway outdoor flashed with Maersk specific Wirepas stack
PART=SRG0107.00,SERIALBS19300004,PRODUCT=SRG0107,NORDIC1_TYPE=NINAB3,NORDIC2_TYPE=NINAB3,STACK1_TYPE=WP,STACK2_TYPE=WP,STACK1_VERSION=V4.0.50-Maersk,STACK2_VERSION=V4.0.50-Maersk

# Kura

Include all Kura spefic add-ons and configuration files

## Kura configuration

Kura configuration is now generated automatiaclly by the provisioning system

## LTE modem management

Kura (Java) module needed to configure the ppp interface for the following modems:
1. Quectel EC25
2. Quectel BG96
