# omg-metrics

OpenShift must-gather metrics analyser.

The analyser will process metrics collected by [must-gather(TODO)](https://github.com/openshift/must-gather) and leave it available on Promtheus tsdb.


## Commands

TODO: see Makefile to get started =)


## Know issues

- On the importer using remote reader for InfluxDB, Prometheus seems to be "don't know" the metrics that was not collected by them. So, I needed to restart the Prometheus container to force this read from remote.