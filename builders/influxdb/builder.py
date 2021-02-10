from __future__ import print_function
from datetime import datetime
import sys, os, logging
import json
from os import listdir
from os.path import (
    isfile as p_isfile,
    join as p_join
)
from influxdb import InfluxDBClient
from argparse import ArgumentParser


class TSDB(object):
    def __init__(self,
                 dbHost=os.getenv("INFLUXDB_HOST", "influxdb"),
                 dbPort=8086):

        self.dbHost = dbHost
        self.dbPort = dbPort
        self.dbc = self.init_TSDB()

    def init_TSDB(self):
        try:
            return InfluxDBClient(host=self.dbHost,
                                port=self.dbPort,
                                ssl=False,
                                verify_ssl=False)
        except:
            return None

    def use(self, dbname):
        self.dbc.switch_database(dbname)

    def write_data_points(self, json_body, batch_size=0):
        self.dbc.write_points(json_body,
                              batch_size=batch_size,
                              time_precision='s')
    
    def prom_metric_to_influxdb(self, series):
        """ Make InfluxDB payload and write to DB """
        influx_body = []
        try:
            for s in series:
                if "metric" not in s:
                    continue
                dpoint = {
                    "measurement": s['metric']['__name__'],
                    "tags": {},
                    "fields": {}
                }

                del s['metric']['__name__']

                for mk in s['metric']:
                    dpoint['tags'][mk] = s['metric'][mk]
                
                dpoint['time'] = datetime.fromtimestamp(s['value'][0]).isoformat('T', 'seconds')
                dpoint['fields']['value'] = float(s['value'][1])

                influx_body.append(dpoint)

        except Exception as e:
            logging.error("ERR seriesToInfluxDB(): {}".format(e))
            pass

        return influx_body

    def parser(self, series):
        try:
            try:
                series_influx = self.prom_metric_to_influxdb(series)
                self.write_data_points(series_influx)
            except Exception as e:
                logging.error("# ERR 2: ", e)
                raise e

        except KeyboardInterrupt:
            quit()
        except Exception as e:
            logging.error("# ERR 1: ", e)
            pass

        return {"status": "success", "total": len(series)}


if __name__ == '__main__':
    parser = ArgumentParser(description='Metrics path.')
    parser.add_argument('-i', '--in', dest='arg_in' , required=True,
                        help='Input file or directory')
    args = parser.parse_args()

    if p_isfile(args.arg_in):
        files = [args.arg_in]
    else:
        path = args.arg_in
        files = ['{}/{}'.format(path, f) \
            for f in listdir(path) \
                if p_isfile(p_join(path, f)) \
            ]

    db = TSDB()
    db.use('prometheus')
    for metric_file in files:
        print(f"Loading metric file: {metric_file}")
        with open(metric_file, 'r') as f:
            data = json.loads(f.read())

        resp = db.parser(data['data']['result'])
        print(json.dumps(resp, indent=4))