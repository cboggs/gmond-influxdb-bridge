from ubuntu:trusty

RUN apt-get update
RUN apt-get install -y python ganglia-monitor

EXPOSE 8649

ADD resources/gmond.conf /etc/ganglia/gmond.conf

#ENTRYPOINT ["/usr/sbin/gmond"]
