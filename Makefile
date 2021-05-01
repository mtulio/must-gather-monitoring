VENV ?= ./.venv

PODMAN ?= podman
NET_PREFIX ?= 10.200.0
CONTAINERS ?= prometheus influxdb
DEFAULT_NET ?= podman

DATA_PATH ?= /mnt/data/tmp/must-gather-monitoring
MUST_GATHER_PATH ?= $(DATA_PATH)/sample-must-gather-small/monitoring/prometheus/


setup:
	test -d $(VENV) || python3 -m venv $(VENV)
	$(VENV)/bin/pip install --upgrade pip
	$(VENV)/bin/pip install -r requirements.txt

setup-data-path:
	test -f ./.env || cp ./.env-default .env

# Runner
all: pod-setup run

## Depends podman>=2.1 and dnsname plugin (https://github.com/containers/dnsname)
pod-prombackfill:
	$(PODMAN) pod create \
		--name prombackfill \
		--hostname prombackfill |true

run-prometheus-backfill: pod-prombackfill
	$(PODMAN) run -it --rm \
		--pod prombackfill \
		-v $(MUST_GATHER_PATH):/data:Z \
		docker.pkg.github.com/mtulio/prometheus-backfill/prometheus-backfill:latest \
		/prometheus-backfill \
		-e json.gz \
		-i /data/ \
		-o "influxdb=http://influxdb:8086=prometheus=admin=Super$ecret"

#> Compose is not working properly
run:
	./podman-manage up

stop:
	./podman-manage down

# run-importer
# run-importer:
# 	cd importers/influxdb && \
# 		test -d $(VENV) || python3 -m venv $(VENV) ; \
# 		$(VENV)/bin/pip3 install -r requirements.txt; \
# 		INFLUXDB_HOST=localhost $(VENV)/bin/python importer.py \
# 			-i $(MUST_GATHER_PATH)

# Cleaner
clean: clean-pods
clean-pods:
	./podman-manage clean
#	 $(PODMAN) pod rm -f $(shell $(PODMAN) pod ps --format="{{ .Id }}" )


# misc
prom-reload:
	curl -XPOST localhost:9090/-/reload

influx-dbs:
	curl -G 'http://localhost:8086/query' --data-urlencode 'q=SHOW DATABASES'
