all: wp-get-fw-version

wp-get-fw-version: main.c
	$(CC) -O0 -o $@ main.c -lpthread -lmesh_api

clean:
	rm -f wp-get-fw-version
