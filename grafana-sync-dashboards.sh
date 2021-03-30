#!/bin/bash

# Sync must-gather collected dashboards to Grafana provisioner dashboard directory

MUST_GATHER_DASHBOARD=${1}
GRAFANA_FOLDER=${2:-'must-gather'}

if [[ -z ${MUST_GATHER_DASHBOARD} ]]; then
    echo 'ARGV1 was not set to grafana dashboard source dir. Eg:'
    echo "${0} data/must-gather/monitoring/grafana/"
    exit 1
fi

for DASH in $(ls ${MUST_GATHER_DASHBOARD}/dashboard_*.json); do
    echo "Converting $DASH to provisioner";
    NAME=$(basename ${DASH} |sed 's/dashboard_//')
    cat ${DASH} |jq .dashboard > "./grafana/dashboards/${GRAFANA_FOLDER}/${NAME}"
done
