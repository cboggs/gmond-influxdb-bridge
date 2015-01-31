#!/bin/bash

p() { 
    echo -e "${1}" 
}

p "Killing and cleaning cboggs-influxdb* containers...\n"
docker ps | grep cboggs-influxdb | awk '{ print $1 }' | xargs docker kill
docker ps -a | grep cboggs-influxdb | awk '{ print $1 }' | xargs docker rm
