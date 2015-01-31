from ubuntu:trusty

RUN apt-get update
RUN apt-get install -y wget

RUN wget http://s3.amazonaws.com/influxdb/influxdb_latest_amd64.deb
RUN sudo dpkg -i influxdb_latest_amd64.deb

EXPOSE 8083
EXPOSE 8086

ENTRYPOINT ["/opt/influxdb/current/influxdb", "--config", "/opt/influxdb/shared/config.toml"]
