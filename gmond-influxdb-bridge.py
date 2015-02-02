#!/usr/bin/python

import argparse
import json
import socket
import time
from influxdb import InfluxDBClient
from io import StringIO, BytesIO
from lxml import etree
from telnetlib import Telnet

argparser = argparse.ArgumentParser()

argparser.add_argument('-d', '--debug', help="Set debug level - the higher the level, the further down the rabbit hole...")
argparser.add_argument('-H', '--hosts', help="Comma-separated list of gmond hosts to poll")
argparser.add_argument('-T', '--timeout', help="Connection timeout in seconds")

argparser.parse_args()
args = argparser.parse_args()

if args.hosts:
    gmond_hosts = args.hosts.split(',')
else:
    ERR ("--hosts is required.")

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
    metrics = metrics.difference(metrics_blacklist)

    for metric_name in metrics:
        metric_data = {'name': metric_name, 'columns': columns, 'points': [] }
        for metric_elem in root_elem.findall(".//METRIC[@NAME='{0}']".format(metric_name)):
            metric_value = metric_elem.attrib['VAL']
            metric_type = metric_elem.attrib['TYPE']
            # findall() because I don't trust gmond to always report EXTRA_ELEMENTs in the same order
            group = next(metric_elem.iterfind("EXTRA_DATA/EXTRA_ELEMENT[@NAME='GROUP']")).attrib['VAL']
            host_name=metric_elem.getparent().attrib['NAME']
            points = [cluster_name, host_name, metric_value, group, epoch_time]
            metric_data['points'].append(points)
        payload.append(metric_data)

epoch_time = int(time.time())
columns = ["cluster", "hostname", "value", "group", "time"]
metrics_blacklist = set(["machine_type", "os_release", "gexec", "os_name"])
payload = []

if args.timeout:
    timeout = args.timeout
else:
    timeout = 3

D (1, "Hosts: {0}".format(gmond_hosts))

for host in gmond_hosts:
    xml_data = get_xml_data(host, timeout)


#client = InfluxDBClient('192.168.59.103', 58086, 'root', 'root', 'test')
#client.create_database('test')
#client.write_points(payload)
