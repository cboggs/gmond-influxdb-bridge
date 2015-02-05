# gmond-influxdb-bridge
Simple bridge app to convert gmond output to Influxdb-friendly data points.

## If It's a Pain, Something's Wrong
I'm an Ops guy. Or an Infra-nerd. Or a CLI junkie. Whatever you want to call it, I spend all my time poking around the internals of some kind of mass of servers. When my tools suck, I stop using them.

If this particular tool isn't easy to use, easy to automate, and easy to forget about after it's setup, then I've done something wrong and you *really* ought to open an issue. Pull requests are always welcome, too!

## Why?
InfluxDB + Grafana = Awesome

gmond system metrics + gmond plugins = Awesome

This is my attempt to bridge two of my favorite Awesomes.

## Dependencies
`sudo apt-get install libxml2-dev libxslt1-dev`
`sudo pip install influxdb lxml`

(Optional: an accessible Docker host)

## Test Drive
If you have a Docker host handy:
```
scripts/build.sh && scripts/run.sh
./gmond-influxdb-bridge.py -H your_docker_host --db_host your-docker_host \
  --db_port 58086 --db_user root --db_pass root --db_name test --create_db -I 15
```

Then just navigate to your_docker_host:5080 in your favorite browser and voila!

## What It Should Do
This tool works fine when pointed at multiple hosts whose gmond instances each contain metrics for a single host.

I've not yet tested a single instance of gmond-influxdb-bridge pointing at multiple gmond collector hosts to collect multi-cluster-wide metrics. Should you try it and find it lacking, you can run multiple instances of gmond-influxdb-bridge as a workaround (for now).

## What's Still to Come
- Read a config file
- Allow custom ports per host
- Test multi-cluster-wide collection via gmond collector hosts (will add option for this in Docker scripts)
- Use standard socket library instead of telnet (slow-brain moment led me to libtelnet... I don't try to understand why)
- Configurable parallelism (should the need arise due to a single instance being too slow to handle many/large clusters)
