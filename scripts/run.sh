#!/bin/bash

p() { 
    echo -e "${1}" 
}

p "Running cboggs-influxdb container...\n"
docker run -d --name cboggs-influxdb -p 8083:58083 -p 8086:58086 cboggs-influxdb

p "\nRunning cboggs-influxdb-bridge container...\n" 
docker run -d --name cboggs-influxdb-bridge --link cboggs-influxdb:influxdb cboggs-influxdb-bridge
