#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
grafana-dash-fixes will look to "desired" state
of the dashboard to be successfull loaded on a local
Grafana environment.
Example of changes:
- payload returned by API should be contain the value of .dashboard
- refresh variables should be reloaded when time range has changed

Usage: cat dashboard.json | python3 grafana-dash-fixes.py

{License_info}
"""

import sys
import os
import json
import logging


def extract_dashboard_payload(data):
    """ Extract .dashboard from raw Grafana API response """
    try:
        return data['dashboard']
    except KeyError as e:
        return {
            "errorMessage": e,
            "error": "Error extracting .dashboard from current payload"
        }
    except Exception as e:
        raise e


def fix_refresh_behavior(data):
    """
    Fix Dashboard variables refresh method from "On Dashboard Load" to
    "On Time Range Change" to automatic discover new variables
    when exploring old data.
    PR opened to fix it:
    https://github.com/openshift/cluster-monitoring-operator/pull/1097
    """
    def_refresh = 2
    for t in data['templating']['list']:
        if t['query'].startswith('label_values'):
            logging.debug(f"Updating refresh behavior for variable {t['name']} from value {t['refresh']} to {def_refresh}")
            t['refresh'] = 2
    return data


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s: %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S')

    try:
        data = sys.stdin.readlines()
        payload = extract_dashboard_payload(json.loads(data[0]))
        payload = fix_refresh_behavior(payload)
        print(json.dumps(payload))
    except Exception as e:
        logging.eror(e)
        sys.exit(1)
