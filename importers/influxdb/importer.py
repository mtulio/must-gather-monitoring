import sys
import os
import logging
import json
from datetime import datetime
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
    
    def prom_query_to_influxdb(self, series):
        """
        Make InfluxDB payload and write to DB.
        /api/v1/query will return a vector
        """
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
            logging.error("ERR prom_query_to_influxdb(): {}".format(e))
            pass

        return influx_body

    def prom_range_to_influxdb(self, series):
        """
        Make InfluxDB payload and write to DB.
        /api/v1/query_range will return a matrix
        """
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

                for v in s['values']:
                    dpoint['time'] = datetime.fromtimestamp(v[0]).isoformat('T', 'seconds')
                    dpoint['fields']['value'] = float(v[1])
                    influx_body.append(dpoint)

        except Exception as e:
            logging.error("ERR prom_range_to_influxdb(): {}".format(e))
            pass

        return influx_body

    def parser(self, series, resultType=None):
        try:
            try:
                if resultType == "vector":
                    series_influx = self.prom_query_to_influxdb(series)
                elif resultType == "matrix":
                    series_influx = self.prom_range_to_influxdb(series)
                else:
                    print(f"Unable to parse. resultType not found on payload: {resultType}")
                    return
                self.write_data_points(series_influx)
            except Exception as e:
                logging.error("# ERR 2: ", e)
                raise e

        except KeyboardInterrupt:
            quit()
        except Exception as e:
            logging.error("# ERR 1: ", e)
            pass

        return {"status": "success", "totalMetricsReceived": len(series), "totalPointsSaved": len(series_influx)}


if __name__ == '__main__':
    parser = ArgumentParser(description='Metrics path.')
    parser.add_argument('-i', '--in', dest='arg_in' , required=True,
                        help='Input file or directory')
    args = parser.parse_args()

    if os.path.isfile(args.arg_in):
        files = [args.arg_in]
    else:
        path = args.arg_in
        files = ['{}/{}'.format(path, f) \
            for f in os.listdir(path) \
                if os.path.isfile(os.path.join(path, f)) \
            ]

    db = TSDB()
    db.use('prometheus')
    for metric_file in files:
        print(f"Loading metric file: {metric_file}")
        with open(metric_file, 'r') as f:
            data = json.loads(f.read())

        resp = db.parser(data['data']['result'], resultType=data['data']['resultType'])
        print(json.dumps(resp, indent=4))