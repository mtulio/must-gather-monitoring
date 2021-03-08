# must-gather-monitoring

Collect monitoring information from the OpenShift cluster, monitoring stackm [using must-gather](https://github.com/openshift/must-gather).

Currently the must-gather-monitoring is build-in on [upstream](https://github.com/openshift/must-gather/pull/214), so it could be a plugin depending how complex or specific it would be.

## Config Variables

`GAHTER_MONIT_START_DATE`: date string (date -d). Default: "7 days ago".

`GAHTER_MONIT_QUERY_STEP`: metric resolution to get from Prometheus. Default: "1m".

`GATHER_MONIT_CUSTOM_METRICS`: list of additional metrics name to be collected. Default: Undefined

`GATHER_MONIT_DISCOVERY_GRAFANA`: manage Grafana metrics discovery, 'no' is disabled. Default: != 'no'

`GATHER_MONIT_DISCOVERY_PREFIXES`: discovery metrics by prefixes. Default: ''


## Usage

- Create the optional ConfigMap configuration

NOTE: See [samples](#Samples) to check variables to set

~~~bash
oc create configmap must-gather-env -n openshift-monitoring --from-file=env=env
~~~

- Run the must-gather

~~~bash
oc adm must-gather --image=quay.io/rhn_support_mrbraga/must-gather:${MG_VER} -- gather_monitoring
~~~

### Samples

- Gather last 15 days of metrics with metrics resolution of `5m` (it may broke dashboards that needs high resolutions)

~~~bash
cat <<EOF> ./env
GAHTER_MONIT_START_DATE="15 days ago"
GAHTER_MONIT_QUERY_STEP="5m"
EOF
~~~

- Collect custom metrics with prefixes `etcd_disk_`, `apiserver_flowcontrol_`

~~~bash
cat << EOF > ./env
GATHER_MONIT_DISCOVERY_PREFIXES="etcd_disk_
apiserver_flowcontrol_"
EOF
~~~

- Collect metrics with exactly name

~~~bash
cat << EOF > ./env
GATHER_MONIT_CUSTOM_METRICS="up"
EOF
~~~

- Enable/disable Grafana metrics discovery

Disabling Grafana metrics discovery may save data collected, it will be usefull to collect specific metrics (Eg: using `GATHER_MONIT_DISCOVERY_PREFIXES`)

~~~bash
cat << EOF > ./env
GATHER_MONIT_DISCOVERY_GRAFANA="no"
GATHER_MONIT_CUSTOM_METRICS="apiserver_flowcontrol_"
EOF
~~~

