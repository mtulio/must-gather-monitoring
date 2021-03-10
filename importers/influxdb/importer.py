# Unefficient way to import metrics from Prometheus to InfluxDB.
# TODO: need to refact to use less memory

import sys
import os
import logging
import json
from datetime import datetime
from influxdb import InfluxDBClient
from argparse import ArgumentParser
from multiprocessing import Queue, queues
import queue
from threading import Thread
import time


global gtimeout
gtimeout = 30
qMaxSize = 1000000

class TSDB(object):
    def __init__(self,
                 dbHost=os.getenv("INFLUXDB_HOST", "influxdb"),
                 dbPort=8086):

        self.dbHost = dbHost
        self.dbPort = dbPort
        self.dbc = self.init_TSDB()

        self.batch_size = qMaxSize
        self.queue = Queue(maxsize=qMaxSize)
        self.qThread = Thread(
            target=self.writer
        )
        self.qThread.start()
        self.qmThread = Thread(target=self.queue_monitor)
        self.qmThread.start()

    def init_TSDB(self):
        try:
            return InfluxDBClient(host=self.dbHost,
                                port=self.dbPort,
                                ssl=False,
                                verify_ssl=False,
                                timeout=gtimeout)
        except:
            return None

    def use(self, dbname):
        self.dbc.switch_database(dbname)

    def _write_data_points(self, json_body, batch_size=0):
        #print("Writing...")
        return self.dbc.write_points(json_body,
                              batch_size=batch_size,
                              time_precision='s')

    def write_data_points(self, json_body, batch_size=0):
        #logging.info(f"Writing data points [{len(json_body)}]...")
        self._write_data_points(json_body, batch_size=batch_size)

    def queue_get_batch(self, batch_size=1000, timeout=gtimeout):
        """
        Get batch objects from the queue
        """
        result = []
        try:
            result = [self.queue.get(timeout=gtimeout)]
            while len(result) < batch_size:
                result.append(self.queue.get(block=False, timeout=gtimeout))
        except queue.Empty:
            pass
        except Exception as e:
            logging.error(e)
            pass
        return result

    def writer(self):
        try:
            while True:
                self.write_data_points(self.queue_get_batch())
        except KeyboardInterrupt:
            pass

    def queue_monitor(self):
        try:
            while True:
                logging.info(f"Queue Size: {self.queue.qsize()} ({sys.getsizeof(self.queue)})")
                time.sleep(30)
        except KeyboardInterrupt:
            pass 

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

                #del s['metric']['__name__']
                for mk in s['metric']:
                    dpoint['tags'][mk] = s['metric'][mk]

                dpoint['time'] = datetime.fromtimestamp(s['value'][0]).isoformat('T', 'seconds')
                dpoint['fields']['value'] = float(s['value'][1])

                #influx_body.append(dpoint)
                self.write_data_points(dpoint)

        except Exception as e:
            logging.error("ERR prom_query_to_influxdb(): {}".format(e))
            pass

        return influx_body

    def prom_range_to_influxdb(self, series):
        """
        Make InfluxDB payload and write to DB.
        /api/v1/query_range will return a matrix
        """
        influx_body = [] # now is dummy
        try:
            for s in series: # could be processed in paralllel
                if "metric" not in s:
                    continue

                name = s['metric']['__name__']
                #del s['metric']['__name__']
                tags = {}
                for mk in s['metric']:
                    tags[mk] = s['metric'][mk]

                for v in s['values']:
                    dpoint = {
                        "measurement": name,
                        "tags": tags,
                        "fields": {}
                    }
                    dpoint['time'] = datetime.fromtimestamp(v[0]).isoformat('T', 'seconds')
                    dpoint['fields']['value'] = float(v[1])

                    #influx_body.append(dpoint)
                    self.queue.put(dpoint)

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
                #self.write_data_points(series_influx)
            except Exception as e:
                logging.error("# ERR 2: ", e)
                return {
                    "status": "error",
                    "errCode": "parser2",
                    "message": e
                }
                raise e

        except KeyboardInterrupt:
            return {
                "status": "calceled"
            }
        except Exception as e:
            logging.error("# ERR 1: ", e)
            return {
                "status": "error",
                "errCode": "parser1",
                "message": e
            }
            pass

        return {
            "status": "success",
            "totalMetricsReceived": len(series),
            "totalPointsSaved": len(series_influx)
        }


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s: %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S')


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
        logging.info(f"Loading metric file: {metric_file}")
        with open(metric_file, 'r') as f:
            # TODO: very low performance, should stream the messages to the processor
            data = json.loads(f.read())
            db.parser(data['data']['result'], resultType=data['data']['resultType'])
            #print(json.dumps(resp, indent=4))
            logging.info(f"Qlen: {db.queue.qsize()}")
            time.sleep(gtimeout)

    logging.info("Pausing...")
    db.qThread.join()
    db.qmThread.join()
    logging.info(f"Finish...wait {gtimeout}s")
    time.sleep(gtimeout)
