#!/usr/bin/python

import argparse
import influxdb
import json
import re
import socket
import time
from lxml import etree
from os import path
from telnetlib import Telnet

argparser = argparse.ArgumentParser()

argparser.add_argument('-d', '--debug', help="Set debug level - the higher the level, the further down the rabbit hole...")
argparser.add_argument('-f', '--config', help="Config file to load")

argparser.parse_args()
args = argparser.parse_args()

if not args.config:
    print "Could not load module 'telepathy'.\nPlease specify a configuration file via -f"
    exit(1)

def D(level, msg):
    if args.debug and int(args.debug) >= level:
        print "DEBUG{0} :: {1}".format(level, msg)

def INFO(msg):
    print "INFO :: {0}".format(msg)

def WARN(msg):
    print "WARN :: {0}".format(msg)

def ERR(msg):
    print "ERROR :: {0}".format(msg)

def ERREXIT(msg):
    print "ERROR :: {0}".format(msg)
    exit(1)

def parse_config(config_filename):
    # hat tip to riquetd for code to parse comments out of json config files
    comment_re = re.compile(
        '(^)?[^\S\n]*/(?:\*(.*?)\*/[^\S\n]*|/[^\n]*)($)?',
        re.DOTALL | re.MULTILINE
    )

    try:
        with open(config_filename) as f:
            content = ''.join(f.readlines())
            match = comment_re.search(content)
            while match:
                content = content[:match.start()] + content[match.end():]
                match = comment_re.search(content)

            print content
            config_data = json.loads(content)
            f.close()

    except ValueError as e:
        ERR ("Failed to load config, invalid JSON:")
        ERREXIT ("  {0}".format(e))

    for val in ['hosts', 'db']:
        if not val in config_data:
            ERREXIT ("missing '{0}' config value - exiting.".format(val))
    
    for val in ['host', 'port', 'name', 'user', 'pass']:
        if not val in config_data['db']:
            ERREXIT ("missing db['{0}'] config value - exiting.".format(val))
            
    return config_data

def get_xml_data(hostname, timeout):
    xml_data = None

    try:
        t = Telnet()
        t.open(hostname, 8649, timeout)
    except socket.timeout:
        ERR ("timeout connecting to host {0}".format(hostname))
    except socket.gaierror:
        ERR ("host not found: {0}".format(hostname))
    except socket.error:
        ERR ("could not connect to host - connection refused: {0}".format(hostname))
    else:
        D (1, "successfully connected to host {0}".format(hostname))
        try:
            xml_data = t.read_all()
        except:
            ERR ("couldn't read data from host {0}".format(hostname))
        else:
            D (3, "XML dump:\n{0}".format(xml_data))
            t.close()
            D (1, "connection to {0} closed".format(hostname))

    return xml_data

def parse_metrics(xml_data, payload):
    metrics = set([])
    root_elem = etree.fromstring(xml_data)
    cluster_name = root_elem[0].attrib['NAME']

    # Build a unique set of metric names found in any host whose metrics are collected
    #  by the current gmond_host. Should allow a single instance of the bridge to poll 
    #  the collector hosts for multiple clusters without forcing a metrics set on them
    for metric_elem in root_elem.findall(".//METRIC"):
        metrics.add(metric_elem.attrib['NAME'])

    # Dump any metrics are blacklisted (usually just values that aren't number types)
    metrics -= metrics_blacklist
    D (2, "metrics found: {0}\n{1}".format(len(metrics), metrics))

    for metric_name in metrics:
        metric_data = {'name': metric_name, 'columns': columns, 'points': [] }
        for metric_elem in root_elem.findall(".//METRIC[@NAME='{0}']".format(metric_name)):
            metric_type = metric_elem.attrib['TYPE']
            metric_value = sanitize_metric(metric_elem.attrib['VAL'], metric_type)
            # findall() because I don't trust gmond to always report EXTRA_ELEMENTs in the same order
            group = next(metric_elem.iterfind("EXTRA_DATA/EXTRA_ELEMENT[@NAME='GROUP']")).attrib['VAL']
            host_name=metric_elem.getparent().attrib['NAME']
            points = [cluster_name, host_name, metric_value, group, epoch_time]
            D (3, "host={0} : group={1} : metric_name={2} : metric_value={3} : metric_type={4} : val_class={5}".format(host_name, group, metric_name, metric_value, metric_type, metric_value.__class__.__name__))
            metric_data['points'].append(points)
        payload.append(metric_data)

def sanitize_metric(value, datatype):
    D (3, "sanitize_metric: datatype = {0}".format(datatype))
    if datatype == "float" or datatype == "double":
        D (3, "converting to float")
        return float(value)
    elif datatype == "uint16" or datatype == "uint32":
        D (3, "converting to int")
        return int(value)
    else:
        WARN ("non-number value detected, which is almost certainly a bug in gmond-influxdb-bridge - you should talk to github.com/cboggs")
        return value

def push_metrics(db_host, db_port, db_user, db_pass, db_name, payload):
    D (1, "db_host={0} : db_port={1} : db_user={2} : db_pass={3} : db_name={4}".format(db_host, db_port, db_user, db_pass, db_name))
    client = influxdb.InfluxDBClient(db_host, db_port, db_user, db_pass, db_name)

    try:
        client.write_points(payload, 's')
    except:
        ERR ("could not write data points to InfluxDB")
    else:
        D (1, "successfully wrote data points to InfluxDB")

config = parse_config(args.config)

gmond_hosts = config['hosts']
metrics_blacklist = set(config['metrics_blacklist'])
columns = config['columns']
interval = config['interval']
timeout = config['timeout']
db = config['db']

INFO ("bridge starting up")
D (1, "gmond_hosts: {0}".format(gmond_hosts))
D (1, "metrics_blacklist: {0}".format(metrics_blacklist))
D (1, "columns: {0}".format(columns))
D (1, "interval: {0}".format(interval))
D (1, "timeout: {0}".format(timeout))
D (1, "db connection: http://{0}:{1}/db/{2}/series?u={3}&p={4}".format(db['host'], db['port'], db['name'], db['user'], db['pass']))

while True:
    epoch_time = int(time.time())
    D (1, "epoch time: {0}".format(epoch_time))
    payload = []

    for host in gmond_hosts:
        xml_data = get_xml_data(host, timeout)
        if xml_data:
            parse_metrics(xml_data, payload)
        else:
            WARN ("no data found on host {0}".format(host))

    if len(payload):
        D (1, "pushing metrics to InfluxDB")
        push_metrics(db['host'], db['port'], db['user'], db['pass'], db['name'], payload)

    elapsed_time = int(time.time()) - epoch_time
    D (1, "elapsed time: {0}s".format(str(elapsed_time)))

    # adjust sleep time in an attempt to keep a consistent publish interval
    # don't sleep at all if elapsed_time > interval to minimize loss of resolution
    if elapsed_time < interval:
        adjusted_sleep = interval - elapsed_time
        D (1, "sleep time adjusted to {0}s".format(str(adjusted_sleep)))
        time.sleep(adjusted_sleep)
    else:
        WARN ("elapsed time >= polling interval, skipping sleep (you may want to run multiple instances of gmond-influxdb-bridge, each polling fewer gmonds)\n")
