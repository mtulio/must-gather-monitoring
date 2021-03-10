VENV ?= ./.venv

PODMAN ?= sudo podman
NET_PREFIX ?= 10.200.0
CONTAINERS ?= prometheus influxdb

MUST_GATHER_PATH ?= $(PWD)/data/sample-must-gather/monitoring/prometheus/

IMAGE_PROMETHEUS ?= prom/prometheus:v2.24.1
IMAGE_GRAFANA ?= grafana/grafana:7.4.3
IMAGE_INFLUXDB ?= influxdb:1.8.0-alpine
IMAGE_INFLUXUI ?= chronograf:1.8.8-alpine

DEFAULT_NET ?= podman

setup:
	test -d $(VENV) || python3 -m venv $(VENV)
	$(VENV)/bin/pip install --upgrade pip
	$(VENV)/bin/pip install -r requirements.txt
	
# Runner
all: pod-setup run

## Depends podman>=2.1 and dnsname plugin (https://github.com/containers/dnsname)
pod-prometheus:
	$(PODMAN) pod create \
		--name prometheus \
		--hostname prometheus \
		-p 9090:9090

pod-grafana:
	$(PODMAN) pod create \
		--name grafana \
		--hostname grafana \
		-p 3000:3000

pod-influxdb:
	$(PODMAN) pod create \
		--name influxdb \
		--hostname influxdb \
		-p 8086:8086 \
		-p 8888:8888

pods-setup: pod-prometheus pod-grafana pod-influxdb
	$(PODMAN) pod create --name data-house --network $(DEFAULT_NET) |true

run-stack: run-prometheus run-influxdb run-influxdb-ui run-grafana
deploy-stack-local: pods-setup run-stack

run-prometheus:
	$(PODMAN) run -d \
		--pod prometheus \
		-v ./data/prometheus:/prometheus:z \
		-v ./prometheus/etc:/etc/prometheus:z \
		--restart always $(IMAGE_PROMETHEUS) \
		--web.enable-lifecycle \
		--config.file=/etc/prometheus/prometheus.yml

run-grafana:
	$(PODMAN) run -d \
		--pod grafana \
		-v ./data/grafana:/var/lib/grafana:z \
		-e GF_SECURITY_ADMIN_PASSWORD=admin \
		--restart always $(IMAGE_GRAFANA)

run-influx: run-influxdb run-influxdb-uid
run-influxdb:
	$(PODMAN) run -d \
		--pod influxdb \
		-e INFLUXDB_ADMIN_ENABLED=true \
		-e INFLUXDB_DB=prometheus \
		-e INFLUXDB_ADMIN_USER=admin \
		-e INFLUXDB_ADMIN_PASSWORD=superp@$ \
		-v ${PWD}/data/influxdb:/var/lib/influxdb:z \
		--restart always $(IMAGE_INFLUXDB)

run-influxdb-ui:
	$(PODMAN) run -d \
		--pod influxdb \
		-v chronograf:/var/lib/chronograf \
		--restart always $(IMAGE_INFLUXUI)

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
clean: clean-containers clean-pods
clean-all-containers:
	$(PODMAN) rm -f $($(PODMAN) ps |awk '{print$1}' |grep -v ^C) | true

clean-pods:
	#$(PODMAN) pod rm $($(PODMAN) pod ls --format "{{ .Id }}") | true
	$(PODMAN) pod rm -f $($(PODMAN) pod ps --format="{{ .Id }}" )

clean-grafana:
	$(PODMAN) rm -f grafana |true

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
