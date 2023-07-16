# must-gather-monitoring stack

> This project is inactive

must-gather-monitoring will deploy locally a monitoring stack (Grafana and Prometheus/remote storage) backfilling the data collected by [OpenShift must-gather monitoring](https://github.com/mtulio/must-gather-monitoring/tree/master/must-gather) to be explored 'out of the box'.

The following projects are used on this stack:
- Prometheus
- InfluxDB (as remote storage)
- Grafana
- [OpenShift must-gather](https://github.com/openshift/must-gather/pull/214)
- [Prometheus-backfill](https://github.com/mtulio/prometheus-backfill)

Use cases:
- troubleshooting the OpenShift cluster when you haven't access to monitoring stack
- investigate specific components/metrics using custom dashboards

## Dependencies

- [podman](https://podman.io/)
- [podman-compose](https://github.com/containers/podman-compose) : `pip3 install podman-compose`
- git

## Usage

### Collect metrics

> **IMPORTANT** note: please make sure to use persistent storage AND not query long periods, it can generate a hige amount of data points.

> **IMPORTANT**: don't use it in production clusters if you are uncertain what data need to be collected. No warranty.

The collector will make API calls to query metrics from Prometheus endpoint and save it locally.

To automate the process to collect in OCP environment, you can use the script that is [WIP on PR #214](https://github.com/openshift/must-gather/pull/214).

Extract the script from latest image created by above PR:

```bash
podman create --name local-must-gather quay.io/mtulio/must-gather:latest-pr214
podman cp local-must-gather:/usr/bin/gather-monitoring-data /tmp/gather-monitoring-data
```

Check if script is present on local machine:
```bash
/tmp/gather-monitoring-data -h
```

Remove temp container:
```bash
podman rm -f local-must-gather
```

Now you can explore all possibilities to collect the data from Prometheus (see `-h`).

Some examples:

- To collect all `up` metric and save it on directory `./metrics-up`, run:
```bash
/tmp/gather-monitoring-data --query "up" --dest-dir ./monitoring-metrics
```

- To collect all metrics with prefix `etcd_disk_`, from 1 hour ago and save it on directory `./metrics-etcd`, run:
```bash
/tmp/gather-monitoring-data -s "1 hours ago" -e "now" -o "./metrics-etcd" --query-range-prefix "etcd_disk_"
```

### Load metrics to a local Prometheus deployment

1. Clone this repository: `git clone git@github.com:mtulio/must-gather-monitoring.git`

2. Deploy stack (Prometheus, Grafana and InfluxDB[Prometheus remote storage]) on local environment using podman:

~~~
$ export WORKDIR=/mnt/data/tmp/123456789/
$ ./podman-manage up
~~~

3. Load the metrics [collected](#collect-metrics) to stack using [prometheus-backfill tool](https://github.com/mtulio/prometheus-backfill):

> Set the variable `METRICS_PATH` to the directory where metrics was saved. Ex: `METRICS_PATH="${PWD}/metrics-etcd"`

> When using must-gather to collect metrics, the directory should be similar to: `METRICS_PATH=/path/to/must-gather.local/quay.io-image/monitoring/prometheus`.

~~~bash
podman run --rm --pod must-gather-monitoring \
  -v ${METRICS_PATH}:/data:Z \
  -it quay.io/mtulio/prometheus-backfill \
    /prometheus-backfill -e json.gz -i "/data/" \
    -o "influxdb=http://127.0.0.1:8086=prometheus=admin=admin"
~~~

4. Explore the data on the stack:

- Grafana: http://localhost:3000
- Prometheus: http://localhost:9090


## Keep in touch / How to contribute

Use it! and give us a feedback opening issues or PR.
