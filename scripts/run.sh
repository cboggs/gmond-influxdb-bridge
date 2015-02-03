#!/bin/bash

echo -e "\nRunning cboggs-influxdb-bridge container...\n" 
docker run -d --name cboggs-influxdb-bridge -h cboggs-influxdb-bridge -p 5080:80 -p 58083:8083 -p 58086:8086 -p 8649:8649 cboggs-influxdb-bridge
