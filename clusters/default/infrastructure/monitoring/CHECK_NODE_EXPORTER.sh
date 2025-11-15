#!/bin/bash
# Script to diagnose Node Exporter issues

echo "=== Node Exporter Pod Status ==="
kubectl get pods -n monitoring -l app.kubernetes.io/name=node-exporter

echo -e "\n=== Node Exporter Pod Details ==="
NODE_EXPORTER_POD=$(kubectl get pods -n monitoring -l app.kubernetes.io/name=node-exporter -o jsonpath='{.items[0].metadata.name}')
if [ ! -z "$NODE_EXPORTER_POD" ]; then
    kubectl describe pod -n monitoring $NODE_EXPORTER_POD
    echo -e "\n=== Node Exporter Pod Events ==="
    kubectl get events -n monitoring --field-selector involvedObject.name=$NODE_EXPORTER_POD --sort-by='.lastTimestamp'
else
    echo "No node exporter pod found"
fi

echo -e "\n=== DaemonSet Status ==="
kubectl get daemonset -n monitoring kube-prometheus-stack-prometheus-node-exporter

