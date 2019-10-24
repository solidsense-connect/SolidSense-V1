# SolidSense-V1
Version V1 of the gateway based on CIP

That repo is progressively augmented

# RPMB

The RPMB includes configuration parameters and is exclusively written in factory during the production process.
This is an ASCII string, with a general syntax <KEYWORD>=<VALUE> separated by comma.

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

All the files that are needed to configure Kura and by consequence the many aspects of the gateway. See dedicated file in the Kura directory

## LTE modem management

Kura (Java) module needed to configure the ppp interface
