all: wp-get-fw-version

wp-get-fw-version: main.c mesh_api_lib.a
	$(CC) -O0 -o $@ main.c mesh_api_lib.a -lpthread

clean:
	rm -f wp-get-fw-version
