#!/bin/bash

p() { 
    echo -e "${1}" 
}

p "Building cboggs-influxdb image...\n"
docker build -t cboggs-influxdb ../docker-influxdb
p "\nDone building cboggs-influxdb image\n"

p "Building cboggs-gmond container...\n" 
docker build -t cboggs-gmond ../docker-gmond
p "\nDone building cboggs-gmond image\n"
