#!/usr/bin/python

import argparse
import influxdb
import json
import socket
import time
from lxml import etree
from os import path
from telnetlib import Telnet

argparser = argparse.ArgumentParser()

argparser.add_argument('-d', '--debug', help="Set debug level - the higher the level, the further down the rabbit hole...")
argparser.add_argument('-H', '--hosts', help="Comma-separated list of gmond hosts/IPs to poll")
argparser.add_argument('-T', '--timeout', help="Connection timeout in seconds")
argparser.add_argument('--db_host', help="InfluxDB hostname/IP")
argparser.add_argument('--db_port', help="InfluxDB port")
argparser.add_argument('--db_user', help="InfluxDB username")
argparser.add_argument('--db_pass', help="InfluxDB password")
argparser.add_argument('--db_name', help="InfluxDB database name")
argparser.add_argument('--create_db', help="If db_name does not exist at db_host, create it (requires that db_user and db_pass be admin credentials)", action="store_true")
argparser.add_argument('-I', '--interval', default=15, help="Polling interval in seconds")

argparser.parse_args()
args = argparser.parse_args()

def D(level, msg):
    if args.debug and int(args.debug) >= level:
        print "DEBUG{0} :: {1}".format(level, msg)

def INFO(msg):
    print "INFO :: {0}".format(msg)

def WARN(msg):
    print "WARN :: {0}".format(msg)

def ERR(msg):
    print "ERROR :: {0}".format(msg)

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

def push_metrics(db_host, db_port, db_user, db_pass, db_name, payload, create_db=False):
    D (1, "create_db: {0}".format(args.create_db))
    D (1, "db_host={0} : db_port={1} : db_user={2} : db_pass={3} : db_name={4}".format(db_host, db_port, db_user, db_pass, db_name))
    client = influxdb.InfluxDBClient(db_host, db_port, db_user, db_pass, db_name)

    if create_db:
        try:
            client.create_database(db_name)
        except influxdb.client.InfluxDBClientError:
            D (1, "db {0} already exists, skipping creation".format(db_name))
        except:
            ERR ("could not create database {0} - most likely you haven't provided admin credentials".format(db_name))
        else:
            INFO ("db {0} not found, creating".format(db_name))
            INFO ("created user {0} in db {1}".format(db_user, db_name))
    try:
        client.write_points(payload, 's')
    except:
        ERR ("could not write data points to InfluxDB")
    else:
        D (1, "successfully wrote data points to InfluxDB")
    
if args.hosts:
    gmond_hosts = args.hosts.split(',')
else:
    ERR ("--hosts is required.")
    exit(1)

if not (args.db_host and args.db_port and args.db_user and args.db_pass and args.db_name):
    ERR ("ALL InfluxDB args are required - please consult {0} --help".format(path.basename(__file__)))
    exit(1)
else:
    db_host = args.db_host
    db_port = args.db_port
    db_user = args.db_user
    db_pass = args.db_pass
    db_name = args.db_name

columns = ["cluster", "hostname", "value", "group", "time"]
metrics_blacklist = set(["machine_type", "os_release", "gexec", "os_name"])

if args.timeout:
    timeout = args.timeout
else:
    timeout = 3

INFO ("bridge starting up")
D (1, "hosts: {0}".format(gmond_hosts))
D (1, "blacklisted metrics: {0}".format(metrics_blacklist))
D (1, "columns: {0}".format(columns))

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
        push_metrics(db_host, db_port, db_user, db_pass, db_name, payload, args.create_db)

    D (1, "elapsed time: {0}\n".format(str(time.time() - epoch_time)))

    time.sleep(float(args.interval))
