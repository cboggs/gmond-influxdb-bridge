#!/usr/bin/python

from lxml import etree

data = open('sample-data/gmond-dump.xml')
allthings = data.read()
columns = ["cluster", "hostname", "value", "time"]
payload = []
metrics = set([])

tree = etree.ElementTree(file='sample-data/gmond-dump.xml')
root_elem = tree.getroot()
#print root_elem.tag, root_elem.attrib

for metric_elem in root_elem.findall(".//METRIC"):
    metrics.add(metric_elem.attrib['NAME'])

for m in  metrics:
    for metric_elem in root_elem.findall(".//METRIC[@NAME='{0}']".format(m)):
        print metric_elem.tag, metric_elem.attrib['NAME']
        print metric_elem.getparent().attrib['NAME']
