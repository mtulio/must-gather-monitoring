VENV ?= ./.venv

PODMAN ?= sudo podman
NET_PREFIX ?= 10.200.0
CONTAINERS ?= prometheus influxdb
DEFAULT_NET ?= podman

DATA_PATH ?= $(PWD)/data
MUST_GATHER_PATH ?= $(DATA_PATH)/sample-must-gather-small/monitoring/prometheus/

IMAGE_PROMETHEUS ?= prom/prometheus:v2.24.1
IMAGE_GRAFANA ?= grafana/grafana:7.5.1
IMAGE_INFLUXDB ?= influxdb:1.8.0-alpine
IMAGE_INFLUXUI ?= chronograf:1.8.8-alpine

setup:
	test -d $(VENV) || python3 -m venv $(VENV)
	$(VENV)/bin/pip install --upgrade pip
	$(VENV)/bin/pip install -r requirements.txt

setup-data-path:
	test -d $(DATA_PATH) || mkdir $(DATA_PATH)
	test -d $(DATA_PATH)/prometheus || mkdir $(DATA_PATH)/prometheus
	test -d $(DATA_PATH)/grafana || mkdir $(DATA_PATH)/grafana
	test -d $(DATA_PATH)/influxdb || mkdir $(DATA_PATH)/influxdb
	chmod o+w -R $(DATA_PATH)

# Runner
all: pod-setup run

## Depends podman>=2.1 and dnsname plugin (https://github.com/containers/dnsname)
pod-prometheus:
	$(PODMAN) pod create \
		--name prometheus \
		--hostname prometheus \
		-p 9090:9090 |true

pod-grafana:
	$(PODMAN) pod create \
		--name grafana \
		--hostname grafana \
		-p 3000:3000 |true

pod-influxdb:
	$(PODMAN) pod create \
		--name influxdb \
		--hostname influxdb \
		-p 8086:8086 \
		-p 8888:8888 |true

pod-prombackfill:
	$(PODMAN) pod create \
		--name prombackfill \
		--hostname prombackfill |true

pods-setup: pod-prometheus pod-grafana pod-influxdb pod-prombackfill
	$(PODMAN) pod create --name data-house --network $(DEFAULT_NET) |true

run-stack: run-prometheus run-influxdb run-grafana
deploy-stack-local: setup-data-path pods-setup run-stack

run-prometheus:
	$(PODMAN) run -d \
		--pod prometheus \
		-v $(DATA_PATH)/prometheus:/prometheus:Z \
		-v ./prometheus/etc:/etc/prometheus:Z \
		--restart always $(IMAGE_PROMETHEUS) \
		--web.enable-lifecycle \
		--config.file=/etc/prometheus/prometheus.yml

run-grafana: pod-grafana
	$(PODMAN) run -d \
		--pod grafana \
		-v $(DATA_PATH)/grafana:/var/lib/grafana:Z \
		-v ./grafana/provisioning:/etc/grafana/provisioning:Z \
		-v ./grafana/dashboards:/etc/grafana/dashboards:Z \
		--env-file $(PWD)/.env \
		--restart always $(IMAGE_GRAFANA)

run-influx: run-influxdb run-influxdb-uid
run-influxdb:
	$(PODMAN) run -d \
		--pod influxdb \
		--env-file $(PWD)/.env \
		-v $(DATA_PATH)/influxdb:/var/lib/influxdb:Z \
		--restart always $(IMAGE_INFLUXDB)

run-influxdb-ui:
	$(PODMAN) run -d \
		--pod influxdb \
		-v chronograf:/var/lib/chronograf:Z \
		--restart always $(IMAGE_INFLUXUI)

run-prometheus-backfill: pod-prombackfill
	$(PODMAN) run -it --rm \
		--pod prombackfill \
		-v $(MUST_GATHER_PATH):/data:Z \
		docker.pkg.github.com/mtulio/prometheus-backfill/prometheus-backfill:latest \
		/prometheus-backfill \
		-e json.gz \
		-i /data/ \
		-o "influxdb=http://influxdb:8086=prometheus=admin=Super$ecret"

# importer
IMPORTER_PATH ?= ./importers/influxdb
IMPORTER_BIN ?= $(IMPORTER_PATH)/.venv/bin
IMPORTER_PY ?= $(IMPORTER_BIN)/python
importer-setup:
	test -d $(IMPORTER_PATH)/.venv || python3 -m venv $(IMPORTER_PATH)/.venv
	INFLUXDB_HOST=localhost $(IMPORTER_BIN)/pip install -r $(IMPORTER_PATH)/requirements.txt

IMPORTER_DATASET ?= ./data/must-gather/monitoring/prometheus/
run-importer:
	$(IMPORTER_PY) $(IMPORTER_PATH)/importer.py -i $(IMPORTER_DATASET)

#> Compose is not working properly
run-compose:
	sudo $(VENV)/bin/podman-compose -f container-compose.yaml up -d

# run-importer
# run-importer:
# 	cd importers/influxdb && \
# 		test -d $(VENV) || python3 -m venv $(VENV) ; \
# 		$(VENV)/bin/pip3 install -r requirements.txt; \
# 		INFLUXDB_HOST=localhost $(VENV)/bin/python importer.py \
# 			-i $(MUST_GATHER_PATH)

# Cleaner
clean: clean-pods
clean-containers:
	$(PODMAN) rm -f $(shell $(PODMAN) ps |awk '{print$1}' |grep -v ^C) | true

clean-pods:
	$(PODMAN) pod rm -f $(shell $(PODMAN) pod ps --format="{{ .Id }}" )

clean-grafana:
	$(PODMAN) pod rm -f grafana |true

clean-prometheus:
	$(PODMAN) rm -f prometheus |true

clean-influxdb:
	$(PODMAN) rm -f influxdb |true

clean-influx-ui:
	$(PODMAN) rm -f influxdb-ui |true

# misc
prom-reload:
	curl -XPOST localhost:9090/-/reload

influx-dbs:
	curl -G 'http://localhost:8086/query' --data-urlencode 'q=SHOW DATABASES'
