VENV ?= ./.venv

PODMAN ?= sudo podman
NET_PREFIX ?= 10.200.0
CONTAINERS ?= prometheus influxdb

MUST_GATHER_PATH ?= $(PWD)/data/sample-must-gather/monitoring/prometheus/

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
		-v ./data/prometheus:/prometheus:z \
		-v ./prometheus/etc:/etc/prometheus:z \
		--restart always prom/prometheus:v2.24.1 \
		--web.enable-lifecycle \
		--config.file=/etc/prometheus/prometheus.yml

		# --ip $(NET_PREFIX).10 \
		# --add-host prometheus:$(NET_PREFIX).10 \
		# --add-host influxdb:$(NET_PREFIX).11 \

run-grafana:
	$(PODMAN) run --name=grafana -d \
		--network omg --pod omg \
		-p 3000:3000 \
		-v ./data/grafana:/var/lib/grafana:z \
		-e GF_SECURITY_ADMIN_PASSWORD=admin \
		--restart always grafana/grafana:7.0.1

run-influxdb:
	$(PODMAN) run --name=influxdb -d \
		--network omg --pod omg \
		-p 8086:8086 \
		-e INFLUXDB_ADMIN_ENABLED=true \
		-e INFLUXDB_DB=prometheus \
		-e INFLUXDB_ADMIN_USER=admin \
		-e INFLUXDB_ADMIN_PASSWORD=superp@$ \
		-v ${PWD}/data/influxdb:/var/lib/influxdb:z \
		--restart always influxdb:1.8.0-alpine

		# --ip $(NET_PREFIX).11 \
		# --add-host prometheus:$(NET_PREFIX).10 \
		# --add-host influxdb:$(NET_PREFIX).11 \

run-influxdb-ui:
	$(PODMAN) run --name=influxdb-ui -d \
		--network omg --pod omg \
		-p 8888:8888 \
		-v chronograf:/var/lib/chronograf \
		--restart always chronograf:1.8.8-alpine

#> Compose is not working properly
run-compose:
	sudo $(VENV)/bin/podman-compose -f container-compose.yaml up -d

# run-importer
run-importer:
	cd importers/influxdb && \
		test -d $(VENV) || python3 -m venv $(VENV) ; \
		$(VENV)/bin/pip3 install -r requirements.txt; \
		INFLUXDB_HOST=localhost $(VENV)/bin/python importer.py \
			-i $(MUST_GATHER_PATH)

# Cleaner
clean: clean-containers clean-pods
clean-containers: #clean-prometheus clean-influxdb
	$(PODMAN) rm -f prometheus |true
	$(PODMAN) rm -f influxdb |true

clean-pod:
	$(PODMAN) pod rm omg |true
	$(PODMAN) network rm omg |true

# misc
prom-reload:
	curl -XPOST localhost:9090/-/reload

influx-dbs:
	curl -G 'http://localhost:8086/query' --data-urlencode 'q=SHOW DATABASES'
