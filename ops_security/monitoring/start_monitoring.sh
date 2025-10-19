#!/bin/bash
echo "Starting Prometheus..."
nohup ~/monitoring/prometheus_bin/prometheus \
  --config.file=~/monitoring/prometheus/prometheus.yml \
  --storage.tsdb.path=~/monitoring/prometheus/prom_data \
  > ~/monitoring/prometheus/prom.log 2>&1 &

echo "Starting Blackbox Exporter..."
nohup ~/monitoring/blackbox_exporter/blackbox_exporter \
  --config.file=~/monitoring/blackbox_exporter/blackbox.yml \
  > ~/monitoring/blackbox_exporter/blackbox.log 2>&1 &

echo "Starting Grafana..."
nohup ~/monitoring/grafana-v11.1.0/bin/grafana server \
  --homepath ~/monitoring/grafana-v11.1.0 \
  > ~/monitoring/grafana/grafana.log 2>&1 &

echo "✅ Monitoring stack started successfully!"
