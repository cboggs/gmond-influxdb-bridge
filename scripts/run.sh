#!/bin/bash

p() { 
    echo -e "${1}" 
}

p "Running cboggs-influxdb container...\n"
docker run -d --name cboggs-influxdb -p 58083:8083 -p 58086:8086 cboggs-influxdb

p "\nRunning cboggs-influxdb-bridge container...\n" 
docker run -d --name cboggs-influxdb-bridge --link cboggs-influxdb:influxdb -p 8649:8649 cboggs-influxdb-bridge
