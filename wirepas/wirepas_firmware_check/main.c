/*
 * Wirepas Firmware version check tool
 *
 * Copyright: Josua Mayer <josua@solid-run.com>
 */
#include <signal.h>
#include <stdio.h>
#include <string.h>
#include <sys/types.h>
#include <unistd.h>

#include "wpc.h"

#define MAX_STRING_SIZE 256

void usage(const char *name) {
	fprintf(stderr, "Usage: %s </dev/ttyACM0>\n", name);
}

const char * handle_ret(app_res_e ret) {
	switch (ret) {
		case APP_RES_OK:
			return "Everything is ok";
			break;
		case APP_RES_STACK_NOT_STOPPED:
			return "Stack is not stopped";
			break;
		case APP_RES_STACK_ALREADY_STOPPED:
			return "Stack is already stopped";
			break;
		case APP_RES_STACK_ALREADY_STARTED:
			return "Stack is already started";
			break;
		case APP_RES_INVALID_VALUE:
			return "A parameter has an invalid value";
			break;
		case APP_RES_ROLE_NOT_SET:
			return "The node role is not set";
			break;
		case APP_RES_NODE_ADD_NOT_SET:
			return "The node address is not set";
			break;
		case APP_RES_NET_ADD_NOT_SET:
			return "The network address is not set";
			break;
		case APP_RES_NET_CHAN_NOT_SET:
			return "The network channel is not set";
			break;
		case APP_RES_STACK_IS_STOPPED:
			return "Stack is stopped";
			break;
		case APP_RES_NODE_NOT_A_SINK:
			return "Node is not a sink";
			break;
		case APP_RES_UNKNOWN_DEST:
			return "Unknown destination address";
			break;
		case APP_RES_NO_CONFIG:
			return "No configuration received/set";
			break;
		case APP_RES_ALREADY_REGISTERED:
			return "Cannot register several times";
			break;
		case APP_RES_NOT_REGISTERED:
			return "Cannot unregister if not registered first";
			break;
		case APP_RES_ATTRIBUTE_NOT_SET:
			return "Attribute is not set yet";
			break;
		case APP_RES_ACCESS_DENIED:
			return "Access denied";
			break;
		case APP_RES_DATA_ERROR:
			return "Error in data";
			break;
		case APP_RES_NO_SCRATCHPAD_START:
			return "No scratchpad start request sent";
			break;
		case APP_RES_NO_VALID_SCRATCHPAD:
			return "No valid scratchpad";
			break;
		case APP_RES_NOT_A_SINK:
			return "Stack is not sink";
			break;
		case APP_RES_OUT_OF_MEMORY:
			return "Out of memory";
			break;
		case APP_RES_INVALID_DIAG_INTERVAL:
			return "Invalid diag interval";
			break;
		case APP_RES_INVALID_SEQ:
			return "Invalid sequence number";
			break;
		case APP_RES_INVALID_START_ADDRESS:
			return "Start address is invalid";
			break;
		case APP_RES_INVALID_NUMBER_OF_BYTES:
			return "Invalid number of bytes";
			break;
		case APP_RES_INVALID_SCRATCHPAD:
			return "Scratchpad is not valid";
			break;
		case APP_RES_INVALID_REBOOT_DELAY:
			return "Invalid reboot delay";
			break;
		case APP_RES_INTERNAL_ERROR:
			return "WPC internal error";
			break;
		default:
			return "Error not handled";
			break;
	}
}

int main(int argc, char *argv[]) {
	app_res_e e = APP_RES_INTERNAL_ERROR;
	app_addr_t node_address;
	net_addr_t node_network;
	net_channel_t node_channel;
	uint16_t version[4] = {0};
	char *ttydev = 0;
	pid_t pid;
	int node_address_set = true;
	int node_network_set = true;
	int node_channel_set = true;

	// take single argument (uart device)
	if(argc == 0) {
		// this is really unusual!
		usage("wp-get-fw-version");
		return 1;
	} else if(argc == 1) {
		usage(argv[0]);
		return 1;
	}
	ttydev = argv[1];

	// spawn a child process for Wirepas API calls
	pid = vfork();
	if(pid < 0) {
		// an error occured
		fprintf(stderr, "Error: fork failed with %d.\n", pid);
		return pid;
	} else if(pid == 0) {
		// Child Thread

		// Initialize Mesh API
		e = WPC_initialize(ttydev, 125000);
		if(e != APP_RES_OK) {
			fprintf(stderr, "Error: WPC_initialize(\"%s\") returned %s.\n", ttydev, handle_ret(e));
			// shut down (kills this thread!)
			WPC_close();
			return e;
		}

		// get firmware version
		e = WPC_get_firmware_version(version);
		if(e != APP_RES_OK) {
			fprintf(stderr, "Error: WPC_get_firmware_version(0x%hn) returned %s.\n", version, handle_ret(e));
			// shut down (kills this thread!)
			WPC_close();
			return e;
		}

		// get the node address
		e = WPC_get_node_address(&node_address);
		if(e != APP_RES_OK) {
			fprintf(stdout, "Warning: WPC_get_node_address(0x%x) returned %s.\n",
					node_address, handle_ret(e));
			// Only fail on get_firmware_version
			e = APP_RES_OK;
			node_address_set = false;
		}

		// get the network address
		e = WPC_get_network_address(&node_network);
		if(e != APP_RES_OK) {
			fprintf(stdout, "Warning: WPC_get_network_address(0x%x) returned %s.\n",
					node_network, handle_ret(e));
			// Only fail on get_firmware_version
			e = APP_RES_OK;
			node_network_set = false;
		}

		// get the channel address
		e = WPC_get_network_channel(&node_channel);
		if(e != APP_RES_OK) {
			fprintf(stdout, "Warning: WPC_get_network_channel(0x%x) returned %s.\n",
					node_channel, handle_ret(e));
			// Only fail on get_firmware_version
			e = APP_RES_OK;
			node_channel_set = false;
		}

		// shut down (kills this thread!)
		WPC_close();

		// exit thread (actually never happens)
		_exit(0);
	} else /* if(pid > 0) */ {
		// Parent Thread -- executes after termination of child

		// inspect results
		if(e == APP_RES_OK) {
			char tmpstr[MAX_STRING_SIZE];
			// print firmware version
			fprintf(stdout, "Wirepas Firmware version: %i.%i.%i.%i\n", version[0], version[1], version[2], version[3]);

			// print node address:network:channel
			fprintf(stdout, "Wirepas Network config: %i:%i:%i\n",
					node_address_set ? node_address : -1,
					node_network_set ? node_network : -1,
					node_channel_set ? node_channel : -1);
			// clean exit
			return 0;
		}

		// exit with error code
		return e;
	}
}
