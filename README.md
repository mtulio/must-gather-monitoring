# omg-metrics

OpenShift must-gather metrics analyser.

The analyser will process metrics collected by [must-gather(TODO)](https://github.com/openshift/must-gather) and leave it available on Promtheus tsdb.

## Components

- data-keeper: extract the metrics file (monitoring/prometheus/*.json) from must-gather and call the importer
- p2iimporter: Prometheus to InfluxDB importer - reads JSON (response from API), parse and batch import to InfluxDB

## Commands

TODO: see Makefile to get started =)

## Know issues

- On the importer using remote reader for InfluxDB, Prometheus seems to be "don't know" the metrics that was not collected by them. So, I needed to restart the Prometheus container to force this read from remote.


## TODOs

- improve performance (use less memory) to the importer, maybe use buffers between parser and importer
- data-keeper should extract only the metrics, avoid use extra space
- data-keeper should remove old/processed files
