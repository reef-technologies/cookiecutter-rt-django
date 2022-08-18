FROM prom/node-exporter:latest

COPY entrypoint.sh /
RUN mkdir -p /home/nobody/textfile_collector_metrics

ENTRYPOINT ["/entrypoint.sh"]