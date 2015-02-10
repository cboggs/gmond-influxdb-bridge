#!/bin/bash
echo "127.0.01 cboggs-influxdb-bridge" >> /etc/hosts
service ganglia-monitor start
service apache2 start
service influxdb start
curl -X POST 'http://localhost:8086/db?u=root&p=root -d {"name": "test"}'
while sleep 49; do dd if=/dev/urandom of=/tmp/random.dat bs=1024 count=500k; done
