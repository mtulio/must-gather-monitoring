# must-gather-monitoring stack

must-gather-monitoring will deploy locally a monitoring stack (Grafana and Prometheus/storages) backfilling the data collected by [OpenShift must-gather monitoring](https://github.com/mtulio/must-gather-monitoring/tree/master/must-gather) to be explored 'out of the box'.

The following projects are used on this stack:
- Prometheus
- InfluxDB (as remote storage)
- Grafana
- [OpenShift must-gather](https://github.com/openshift/must-gather/pull/214)
- [Prometheus-backfill](https://github.com/mtulio/prometheus-backfill)

Use cases:
- troubleshooting the OpenShift cluster when you haven't access to monitoring stack
- investigate specific components/metrics using custom dashboards

<!--
## Components

- data-importer: monitor custom storage path looking to extract metrics to must-gather and leave it available to be imported by a backend plugin (influxdb)
1) uploads watcher : container to watch /data/uploads dir and extract metrics files from must-gather.
2) metrics watcher: container to watch /data/metrics gzip metrics' file exported from must-gather
3) backend importer: tsdb parser and importer
4) grafana importer: dashboard importer
- Prometheus: static config reading metrics from remote storage (backfilling metrics to Prometheus, is not available, ATM, so we choosed one simple available RW remote storage: influxdb)
- Grafana: visualize metrics from Promtheus, importing dashboards available on must-gather - and also could have pre-build dashboards
- influxdb: TSDB RW remote storage choosed to backfill metrics exported from Prometheus' on OCP though must-gather
1) influxdb: TSDB
2) chronograf: InfluxDB's UI explorer to InfluxDB importer - reads JSON (response from API), parse and batch import to InfluxDB
-->

## Install

1. clone this repository: `git clone git@github.com:mtulio/must-gather-monitoring.git`

2. Install the dependencies:
dependencies:
- [podman](https://podman.io/)
- [podman-compose](https://github.com/containers/podman-compose) : `pip3 install podman-compose`

3. Collect must-gather data from the OpenShift cluster (with monitoring support, as described on [Usage](#Usage))

## Usage

- Collect the data using [must-gather](./must-gather/README.md)

~~~
oc adm must-gather --image=docker.pkg.github.com/mtulio/must-gather-monitoring/must-gather-monitoring:latest -- gather_monitoring
~~~

- Deploy stack on local environment using podman:

> Point the variable `MUST_GATHER_PATH_LOGS` to the root of must-gather

~~~
$ export WORKDIR=/mnt/data/tmp/123456789/
$ export MUST_GATHER_PATH_LOGS="/path/to/must-gather.local/quay.io-image"
$ ./podman-manage up
~~~

- Load the metrics collected by must-gather to stack using prometheus-backfill tool:

> Point the variable `MUST_GATHER_PATH_METRICS` to the directories that the metrics was exported

~~~bash
export MUST_GATHER_PATH_METRICS=/path/to/must-gather.local/quay.io-image/monitoring/prometheus
podman run --rm --pod must-gather-monitoring \
  -v ${MUST_GATHER_PATH_METRICS}:/data:Z \
  -it quay.io/mtulio/prometheus-backfill \
    /prometheus-backfill -e json.gz -i "/data/" \
    -o "influxdb=http://127.0.0.1:8086=prometheus=admin=admin"
~~~

- Explore the data on the stack:

Grafana: http://localhost:3000

Prometheus: http://localhost:9090

<!--
### Proposal to omg (TODO)

TODO: proposal to integrate with [o-must-gather](https://github.com/kxr/o-must-gather)

prefix: omg monitoring

- deploy <podman|ocp> : deploy stack to podman/ocp
- import <influxdb|grafana|all>: data to stack (Grafana and Influxdb)
- session <list|save> : save current session (MG dir, deployments) to a cache file
-->

## Keep in touch / How to contribute

Use it and give a feedback opening issues or PR, it is always welcome.

### Know issues

- Build a Grafana Dashboard importer that is collected by must-gather
- Importer are taking too long due to amount of data points from some metrics (Eg: container_memory_working_set_bytes). Some metrics has high cardinality, when extracted and tranformed to  payload to be writen to remote, the memory increase too much. Need to review the parser to decrease the time processing and memory usage.
<!--
- data-keeper should extract only the metrics, avoid to use extra space consumption with information non related with monitoring stack
- data-keeper should remove old/processed files
-->
- Grafana DS provisioning is not working properly

### Future ideas

- support more options to backfill the metrics. The project [Prometheus-backfill](https://github.com/mtulio/prometheus-backfill) is responsible for that, so there are more information [here](https://github.com/mtulio/prometheus-backfill#roadmap--how-to-contribute)
- create local tests
- create the grafana importer calling the API to import the dashboards exported by must-gather. It may need to be parsed to remove headers from API.

- create data tenancy exploring the current tools. E.g: Grafana (Org) and Remote storage (splited by databases) could be used as multi-tenant of the data, avoid launching too many instances and allowing to exploring in parallel different data sources (must-gathers). The Prometheus may need to be single-tenant in this ideia

- Create an operator to make easy the deployment of whole stack and decrease time taking for each component, just use the solution:
- split/parser could be decoubled from importer, so we can scale the importer in the case of high amount of metrics
