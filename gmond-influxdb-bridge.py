#!/usr/bin/python

import json
import time
from influxdb import InfluxDBClient
from io import StringIO, BytesIO
from lxml import etree
from telnetlib import Telnet

t = Telnet()
t.open("192.168.59.103", 8649)
xml_data = StringIO(unicode(t.read_all()))
xml_data = t.read_all()
t.close()

epoch_time = int(time.time())
data = open('sample-data/gmond-dump.xml')
allthings = data.read()
columns = ["cluster", "hostname", "value", "group", "time"]
payload = []
metrics = set([])
metrics_blacklist = set(["machine_type", "os_release", "gexec", "os_name"])

root_elem = etree.fromstring(xml_data)
cluster_name = root_elem[0].attrib['NAME']

for metric_elem in root_elem.findall(".//METRIC"):
    metrics.add(metric_elem.attrib['NAME'])

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

client = InfluxDBClient('192.168.59.103', 58086, 'root', 'root', 'test')
#client.create_database('test')
client.write_points(payload)

