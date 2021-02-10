
VENV ?= ./.venv
PODMAN ?= sudo podman
CONTAINERS ?= prometheus influxdb

NET_PREFIX ?= 10.200.0

setup:
	test -d $(VENV) || python3 -m venv $(VENV)
	$(VENV)/bin/pip install --upgrade pip
	$(VENV)/bin/pip install -r requirements.txt
	
# Runner
all: pod-setup run

pod-setup:
	$(PODMAN) network create omg --subnet $(NET_PREFIX).0/24
	$(PODMAN) pod create --name omg --network omg

run: run-prometheus run-influxdb

run-prometheus:
	$(PODMAN) run --name=prometheus -d \
		--network omg --pod omg \
		-p 9090:9090 \
		--ip $(NET_PREFIX).10 \
		--add-host prometheus:$(NET_PREFIX).10 \
		--add-host influxdb:$(NET_PREFIX).11 \
		-v ${PWD}/data/prometheus:/prometheus:z \
		-v ${PWD}/prometheus/etc:/etc/prometheus:z \
		--restart always prom/prometheus:v2.24.1

run-influxdb:
	$(PODMAN) run --name=influxdb -d \
		--network omg --pod omg \
		-p 8086:8086 \
		--ip $(NET_PREFIX).11 \
		--add-host prometheus:$(NET_PREFIX).10 \
		--add-host influxdb:$(NET_PREFIX).11 \
		-e INFLUXDB_ADMIN_ENABLED=true \
		-e INFLUXDB_DB=prometheus \
		-e INFLUXDB_ADMIN_USER=admin \
		-e INFLUXDB_ADMIN_PASSWORD=superp@$ \
		-v ${PWD}/data/influxdb:/var/lib/influxdb:z \
		--restart always influxdb:1.8.0-alpine

#> Compose is not working properly
run-compose:
	sudo $(VENV)/bin/podman-compose -f container-compose.yaml up -d

# run-importer
run-importer:
	cd builders/influxdb && \
		test -d ./.venv || python3 -m venv ./.venv ; \
		./.venv/bin/pip3 install -r requirements.txt; \
		INFLUXDB_HOST=localhost ./.venv/bin/python builder.py -i $(PWD)/data/sample-must-gather2

# Cleaner
clean: clean-containers clean-pods
clean-containers: #clean-prometheus clean-influxdb
	$(PODMAN) rm -f prometheus |true
	$(PODMAN) rm -f influxdb |true

clean-pod:
	$(PODMAN) pod rm omg |true
	$(PODMAN) network rm omg |true
