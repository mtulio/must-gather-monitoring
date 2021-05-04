# Runner using podman-compose
all: run
start: run
run:
	./podman-manage up

stop:
	./podman-manage down

clean:
	./podman-manage clean
#	$(PODMAN) pod rm -f $(shell $(PODMAN) pod ps --format="{{ .Id }}" )

# misc
prom-reload:
	curl -XPOST localhost:9090/-/reload

influx-dbs:
	curl -G 'http://localhost:8086/query' --data-urlencode 'q=SHOW DATABASES'
