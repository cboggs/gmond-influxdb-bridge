from ubuntu:trusty

RUN apt-get update
RUN apt-get install -y python ganglia-monitor apache2 wget

EXPOSE 8649
EXPOSE 8083
EXPOSE 8086
EXPOSE 80

WORKDIR /var/www
RUN wget http://grafanarel.s3.amazonaws.com/grafana-1.9.1.tar.gz
RUN tar -xvzf grafana-1.9.1.tar.gz

WORKDIR /root
RUN wget http://s3.amazonaws.com/influxdb/influxdb_latest_amd64.deb
RUN sudo dpkg -i influxdb_latest_amd64.deb

ADD resources/gmond.conf /etc/ganglia/gmond.conf
ADD resources/grafana.conf /etc/apache2/sites-available/grafana.conf
ADD resources/grafana_config.js /var/www/grafana-1.9.1/config.js
ADD resources/grafana_default_dashboard.json /var/www/grafana-1.9.1/app/dashboards/default.json
ADD resources/spin.sh /root/spin.sh

ENTRYPOINT ["/root/spin.sh"]
