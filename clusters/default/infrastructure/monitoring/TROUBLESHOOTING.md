# Monitoring Stack Troubleshooting Guide

## Common Issues and Solutions

### 1. Check Pod Status

```bash
# Check all pods in monitoring namespace
kubectl get pods -n monitoring

# Watch pods in real-time
kubectl get pods -n monitoring -w
```

### 2. Check Pod Logs

```bash
# Grafana logs
kubectl logs -n monitoring deployment/kube-prometheus-stack-grafana -c grafana

# Prometheus logs
kubectl logs -n monitoring prometheus-kube-prometheus-stack-prometheus-0 -c prometheus

# Loki logs
kubectl logs -n monitoring -l app.kubernetes.io/name=loki

# Promtail logs
kubectl logs -n monitoring -l app.kubernetes.io/name=promtail
```

### 3. Check Pod Details (Events and Status)

```bash
# Grafana pod details
kubectl describe pod -n monitoring -l app.kubernetes.io/name=grafana

# Prometheus pod details
kubectl describe pod -n monitoring prometheus-kube-prometheus-stack-prometheus-0

# Node Exporter (DaemonSet)
kubectl describe pod -n monitoring -l app.kubernetes.io/name=node-exporter
```

### 4. Restart Pods

```bash
# Restart Grafana deployment
kubectl rollout restart deployment -n monitoring kube-prometheus-stack-grafana

# Restart Prometheus StatefulSet
kubectl rollout restart statefulset -n monitoring prometheus-kube-prometheus-stack-prometheus

# Restart Node Exporter DaemonSet
kubectl rollout restart daemonset -n monitoring kube-prometheus-stack-prometheus-node-exporter

# Restart Loki (if using deployment)
kubectl rollout restart deployment -n monitoring loki

# Restart Promtail DaemonSet
kubectl rollout restart daemonset -n monitoring promtail
```

### 5. Delete and Recreate Pods (Force Restart)

```bash
# Delete Grafana pod (will be recreated automatically)
kubectl delete pod -n monitoring -l app.kubernetes.io/name=grafana

# Delete Prometheus pod (StatefulSet will recreate)
kubectl delete pod -n monitoring prometheus-kube-prometheus-stack-prometheus-0

# Delete Node Exporter pod (DaemonSet will recreate)
kubectl delete pod -n monitoring -l app.kubernetes.io/name=node-exporter
```

### 6. Check HelmRelease Status

```bash
# Check FluxCD HelmRelease status
kubectl get helmrelease -n monitoring

# Describe HelmRelease to see errors
kubectl describe helmrelease -n monitoring kube-prometheus-stack
kubectl describe helmrelease -n monitoring loki
kubectl describe helmrelease -n monitoring promtail

# Reconcile HelmRelease manually
flux reconcile helmrelease -n monitoring kube-prometheus-stack
flux reconcile helmrelease -n monitoring loki
flux reconcile helmrelease -n monitoring promtail
```

### 7. Check Services

```bash
# List all services in monitoring namespace
kubectl get svc -n monitoring

# Check service endpoints
kubectl get endpoints -n monitoring
```

### 8. Check Ingress

```bash
# Check Grafana ingress
kubectl get ingress -n monitoring
kubectl describe ingress -n monitoring kube-prometheus-stack-grafana
```

### 9. Common Issues

#### Grafana CrashLoopBackOff
- **Issue**: Datasource configuration error
- **Solution**: Only one datasource can be marked as default. Check `isDefault` flags in datasource configuration.

#### Node Exporter CreateContainerError
- **Issue**: Missing host path mounts or permissions
- **Solution**: Ensure `hostPID: true`, `hostNetwork: true`, and proper volume mounts are configured.

#### Promtail Not Collecting Logs
- **Issue**: Missing RBAC permissions or volume mounts
- **Solution**: Check RBAC rules and ensure `/var/log` is mounted from host.

### 10. Check Resource Usage

```bash
# Check resource usage
kubectl top pods -n monitoring
kubectl top nodes
```

### 11. Check Events

```bash
# Check all events in monitoring namespace
kubectl get events -n monitoring --sort-by='.lastTimestamp'

# Check specific pod events
kubectl get events -n monitoring --field-selector involvedObject.name=<pod-name>
```

### 12. Access Grafana

```bash
# Port forward to access Grafana locally
kubectl port-forward -n monitoring svc/kube-prometheus-stack-grafana 3000:80

# Then access at http://localhost:3000
# Default credentials: admin/admin
```

### 13. Verify Log Collection

```bash
# Check if Promtail is scraping logs
kubectl logs -n monitoring -l app.kubernetes.io/name=promtail | grep -i error

# Check Loki is receiving logs
kubectl logs -n monitoring -l app.kubernetes.io/name=loki | tail -20
```

