# must-gather-monitoring stack

must-gather-monitoring will deploy locally a monitoring stack (Grafana and Prometheus/storages) backfilling the data collected by [OpenShift must-gather](https://github.com/mtulio/must-gather-monitoring/tree/master/must-gather).

The projects used on this stack are:
- Prometheus
- Grafana
- [OpenShift must-gather](https://github.com/openshift/must-gather/pull/214)
- [Prometheus-backfill](https://github.com/mtulio/prometheus-backfill)

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

## Usage

> see more on Makefile to get started =)

- Deploy stack on dev environment (using podman), create pods and run the containers:

~~~
make deploy-stack-local
~~~

### Proposal to omg (TODO)

TODO: proposal to integrate with [o-must-gather](https://github.com/kxr/o-must-gather)

prefix: omg monitoring

- deploy <podman|ocp> : deploy stack to podman/ocp
- import <influxdb|grafana|all>: data to stack (Grafana and Influxdb)
- session <list|save> : save current session (MG dir, deployments) to a cache file

## Know issues

> TODO is not addressed yet to issues

- On the importer using remote reader for InfluxDB, Prometheus' autocomplete seems to "don't known" the metrics that was not collected by them - does not have jobs associated to metrics
- Sometimes, when backfilling directly to influxdb, the Prometheus does not find the metric on remote storage, restarting the Prometheus fixes the issue
- Importer are taking too long and 'eating' memory. Some metrics has high cardinality, when extracted and tranformed to influxdb's payload, the memory increase too much. Need to refact the parser/dbwriter to decrease the time and memory consume.
- data-keeper should extract only the metrics, avoid to use extra space consumption with information non related with monitoring stack
- data-keeper should remove old/processed files
- create the grafana importer calling the API - the exported dashboards may need to be parsed to remove headers from API.

### Future ideas

- Create an operator to make easy the deployment of whole stack and decrease time taking for each component, just use the solution:
- split/parser could be decoubled from importer, so we can scale the importer in the case of high amount of metrics
