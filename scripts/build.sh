#!/bin/bash

p() { 
    echo -e "${1}" 
}

script_dir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd -P)"

p "Building cboggs-influxdb image...\n"
docker build -t cboggs-influxdb ${script_dir}/../docker-influxdb
p "\nDone building cboggs-influxdb image\n"

p "Building cboggs-influxdb-bridge container...\n" 
docker build -t cboggs-influxdb-bridge ${script_dir}/..
p "\nDone building cboggs-influxdb-bridge image\n"
