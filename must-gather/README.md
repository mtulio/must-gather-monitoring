# must-gather-data (Collector)

Collect monitoring information from the OpenShift cluster, monitoring stackm [using must-gather](https://github.com/openshift/must-gather).

Currently the must-gather-monitoring is build-in [WIP on upstream](https://github.com/openshift/must-gather/pull/214), so it could be a plugin depending how complex or specific it would be.

When it is not merged, the build images with must-gather-monitoring scripts is available on [quay.io](https://quay.io/repository/rhn_support_mrbraga/must-gather?tab=tags).

## Config Variables

`GATHER_MONIT_START_DATE`: start date string (rendered by `date -d`)

`GATHER_MONIT_END_DATE`: end date string (rendered by `date -d`)

`GATHER_MONIT_QUERY_STEP`: metric resolution to get from Prometheus. Default: "1m".

`GATHER_PROM_QUERIES_RANGE`: list of valid queries to collect range of data points, based on `start` and `end` variables

`GATHER_PROM_QUERIES`: list of valid queries to collect instant data points

`GATHER_PROM_QUERIES_RANGE_PREFIX`: list of valid metric prefixes to be discovery and collected a query range.

(TODO) `GATHER_MONIT_DISCOVERY_GRAFANA`: manage Grafana metrics discovery, 'no' is disabled. Default: != 'no'

## Usage

- Create the optional ConfigMap configuration

NOTE: See [samples](#Samples) to check variables to set

~~~bash
oc create configmap must-gather-env -n openshift-monitoring --from-file=env=env
~~~

- Run the must-gather

~~~bash
oc adm must-gather --image=quay.io/mtulio/must-gather:${MG_VER} -- gather_monitoring
~~~

- Run the script standalone (require `/must-gather` path)

~~~
export MG_BASE_PATH=./must-gather-metrics

# Set env vars (see Usage section)

bash collection-scripts/gather-monitoring-data
~~~

### Samples

All examples below could be used running in must-gather workflow or locally, the dependency is the environment var that must be properly set on each setup:
- must-gather: uses a configMap
- local: uses a manual environment

#### Customizing start/end

The start, end and resolution can be customized to adjust the range of queries. It will impact directly in the amount of data points and size that will be collected.

- Gather last 15 days of metrics with metrics resolution of `5m` (it may broke dashboards that needs high resolutions)

~~~bash
cat <<EOF> ./env
GAHTER_MONIT_START_DATE="15 days ago"
GAHTER_MONIT_QUERY_STEP="5m"
EOF
~~~

#### Collect metrics from **instant queries**

Goal: collect instant queries from a valid Query

~~~bash
cat << EOF > ./env
GATHER_PROM_QUERIES="prometheus_http_requests_total"
EOF
~~~

#### Collect metrics from **query ranges**

Goal: collect a query range from a valid PromQL query.

~~~bash
cat << EOF > ./env
GATHER_PROM_QUERIES_RANGE="etcd_disk_backend_commit_duration_seconds_bucket"
EOF
~~~

#### Collect metrics from **query ranges by prefixes**

Goal: collect query range from all group(s) of metric(s) from a specific component. Eg: `etcd_disk`

- Collect custom metrics with prefixes `etcd_disk_`, `apiserver_flowcontrol_`

~~~bash
cat << EOF > ./env
GATHER_PROM_QUERIES_RANGE_PREFIX="etcd_disk_
apiserver_flowcontrol_"
EOF
~~~

#### (WIP) Collect metrics from/and dashboards from Grafana

- Enable/disable Grafana metrics discovery

Disabling Grafana metrics discovery may save data collected, it will be usefull to collect specific metrics (Eg: using `GATHER_PROM_QUERIES_RANGE_PREFIX`)

~~~bash
cat << EOF > ./env
GATHER_MONIT_DISCOVERY_GRAFANA="no"
GATHER_PROM_QUERIES_RANGE_PREFIX="apiserver_flowcontrol_"
EOF
~~~

