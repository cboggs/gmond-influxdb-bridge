#!/bin/bash

script_dir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd -P)"

echo -e "Building cboggs-influxdb-bridge container...\n" 
docker build -t cboggs-influxdb-bridge ${script_dir}/..
echo -e "\nDone building cboggs-influxdb-bridge image\n"
