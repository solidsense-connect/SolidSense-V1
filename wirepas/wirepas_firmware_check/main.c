/*
 * Wirepas Firmware version check tool
 * 
 * Copyright: Josua Mayer <josua@solid-run.com>
 */
#include <signal.h>
#include <stdio.h>
#include <sys/types.h>
#include <unistd.h>

#include "wpc.h"

void usage(const char *name) {
	fprintf(stderr, "Usage: %s </dev/ttyACM0>\n", name);
}

int main(int argc, char *argv[]) {
	app_res_e e = APP_RES_INTERNAL_ERROR;
	app_addr_t node_address;
	uint16_t version[4] = {0};
	char *ttydev = 0;
	pid_t pid;

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
		fprintf(stderr, "Error: fork failed with %ld!\n", pid);
		return pid;
	} else if(pid == 0) {
		// Child Thread

		// Initialize Mesh API
		e = WPC_initialize(ttydev, 125000);
		if(e != APP_RES_OK) {
			fprintf(stderr, "Error: WPC_initialize(\"%s\") returned %i!\n", ttydev, e);
			// shut down (kills this thread!)
			WPC_close();
			return e;
		}

		// get firmware version
		e = WPC_get_firmware_version(version);
		if(e != APP_RES_OK) {
			fprintf(stderr, "Error: WPC_get_firmware_version((0x%x) returned %i!\n", version, e);
			// shut down (kills this thread!)
			WPC_close();
			return e;
		}

		// get the node address
		e = WPC_get_node_address(&node_address);
		if(e != APP_RES_OK) {
			fprintf(stderr, "Error: WPC_get_node_address((0x%x) returned %i!\n", node_address, e);
			// shut down (kills this thread!)
			WPC_close();
			return e;
		}

		// shut down (kills this thread!)
		WPC_close();

		// exit thread (actually never happens)
		_exit(0);
	} else /* if(pid > 0) */ {
		// Parent Thread -- executes after termination of child

		// inspect results
		if(e == APP_RES_OK) {
			// print firmware version
			fprintf(stdout, "Firmware version: %i.%i.%i.%i\n", version[0], version[1], version[2], version[3]);

			// print node address
			fprintf(stdout, "Node address: %i\n", node_address);

			// clean exit
			return 0;
		}

		// exit with error code
		return e;
	}
}
