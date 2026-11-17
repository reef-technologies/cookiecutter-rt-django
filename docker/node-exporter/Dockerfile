FROM prom/node-exporter:v1.3.1

COPY entrypoint.sh /
RUN mkdir -p /home/nobody/textfile_collector_metrics

ENTRYPOINT ["/entrypoint.sh"]