#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Deprecated script to use Grafana provisioning
Script to setup custom Datasources on Grafana.
Grafana provisioning was not working properly
when using DS name 'default'.
Issue tracked on https://github.com/grafana/grafana/issues/32460
{License_info}
"""

import os
import json
import logging
import copy
import requests
from requests.auth import HTTPBasicAuth


with open('./env.json', 'r') as f:
    defaults_env = json.loads(f.read())


with open('./base-ds.json', 'r') as f:
    defaults_ds = json.loads(f.read())


def build_ds_prometheus(name='default',
                        url=os.getenv('PROMETHEUS_URL', defaults_env['PROMETHEUS_URL']),
                        isDefault=False
                        ):
    ds = copy.deepcopy(defaults_ds)
    ds['name'] = name
    ds['url'] = url
    ds['type'] = "prometheus"
    ds['isDefault'] = isDefault
    return ds


def build_ds_influxdb(name='influxdb-prom',
                      url=os.getenv('INFLUXDB_URL', defaults_env['INFLUXDB_URL'])):
    ds = copy.deepcopy(defaults_ds)
    ds['name'] = name
    ds['url'] = url
    ds['type'] = "influxdb"
    ds['database'] = os.getenv('INFLUXDB_DB', defaults_env['INFLUXDB_DB'])
    ds['isDefault'] = False
    ds['basicAuth'] = True
    ds['basicAuthUser'] = os.getenv('INFLUXDB_ADMIN_USER', defaults_env['INFLUXDB_ADMIN_USER'])
    ds['basicAuthPassword'] = os.getenv('INFLUXDB_ADMIN_PASSWORD', defaults_env['INFLUXDB_ADMIN_PASSWORD'])
    return ds


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s: %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S')

    gf_url = os.getenv('GF_URL', defaults_env['GF_URL'])
    gf_usr = os.getenv('GF_SECURITY_ADMIN_USER', defaults_env['GF_SECURITY_ADMIN_USER'])
    gf_pass = os.getenv('GF_SECURITY_ADMIN_USER', defaults_env['GF_SECURITY_ADMIN_USER'])
    
    gf_url_ds = (f"{gf_url}/api/datasources")
    gf_auth = HTTPBasicAuth(gf_usr, gf_pass)
    logging.info(f"Using Grafana login user: {gf_usr}")
    logging.info(f"GF DS endpoint: {gf_url_ds}")

    # Create Prometheus DS
    resp = None
    try:
        logging.info("Creating Prometheus Datasource 02")
        ds_prom = build_ds_prometheus(name="must-gather-prometheus", isDefault=True)
        logging.info(f"-> Payload: {ds_prom}")
        resp = requests.post(gf_url_ds, data=ds_prom, auth=gf_auth)
        logging.info(f"-> DS Prometheus creation status code: {resp}")
        if resp.status_code/100 != 2:
            logging.info(resp.text)
    except Exception as e:
        logging.info(f"-> DS Prometheus creation error code: {resp}")
        logging.error(e)
        pass

    # Create InfluxDB DS
    resp = None
    try:
        logging.info("Creating InfluxDB Datasource")
        ds_influxdb = build_ds_influxdb(name="must-gather-influxdb")
        logging.info(f"-> Payload: {ds_influxdb}")
        resp = requests.post(gf_url_ds, data=ds_influxdb, auth=gf_auth)
        logging.info(f"-> DS creation status code: {resp}")
        if resp.status_code/100 != 2:
            logging.info(resp.text)
    except Exception as e:
        logging.info(f"-> DS creation error code: {resp}")
        logging.error(e)
        pass
