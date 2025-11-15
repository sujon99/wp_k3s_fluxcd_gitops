# How to Apply Changes and Restart Ingress-NGINX

Since you're using FluxCD (GitOps), there are two approaches to apply the changes:

## Method 1: GitOps (Recommended - Automatic)

### Step 1: Commit and Push Changes to Git

```bash
# Navigate to your repository
cd "D:\Learning\WordPress in k3s_v2"

# Add the changed files
git add clusters/default/infrastructure/ingress-nginx/helmrelease.yaml
git add clusters/default/infrastructure/ingress-nginx/lua-redirect-plugin.yaml

# Commit the changes
git commit -m "Add Lua plugin to redirect 404 responses to google.com"

# Push to your Git repository
git push
```

### Step 2: Wait for FluxCD to Sync (or Force Reconciliation)

FluxCD will automatically detect the changes and sync them. You can:

**Option A: Wait for automatic sync** (usually happens within the sync interval)

**Option B: Force immediate reconciliation:**
```bash
# Reconcile the infrastructure kustomization
flux reconcile kustomization infrastructure

# Or reconcile the specific HelmRelease
flux reconcile helmrelease ingress-nginx -n ingress-nginx
```

### Step 3: Verify the Changes

```bash
# Check if HelmRelease is updated
kubectl get helmrelease ingress-nginx -n ingress-nginx -o yaml

# Check if ConfigMap is created/updated
kubectl get configmap lua-redirect-plugin -n ingress-nginx -o yaml

# Check ingress-nginx pods status
kubectl get pods -n ingress-nginx

# Check if pods are restarting/updating
kubectl get pods -n ingress-nginx -w
```

### Step 4: Restart Ingress-NGINX Pods (if needed)

The Helm upgrade should automatically restart the pods, but if they don't restart automatically:

```bash
# Restart the ingress-nginx controller deployment
kubectl rollout restart deployment ingress-nginx-controller -n ingress-nginx

# Or delete pods to force recreation
kubectl delete pods -n ingress-nginx -l app.kubernetes.io/component=controller
```

## Method 2: Manual Apply (Without Git)

If you want to apply changes directly without using Git:

### Step 1: Apply the ConfigMap

```bash
kubectl apply -f clusters/default/infrastructure/ingress-nginx/lua-redirect-plugin.yaml
```

### Step 2: Apply the HelmRelease Update

```bash
kubectl apply -f clusters/default/infrastructure/ingress-nginx/helmrelease.yaml
```

### Step 3: Force HelmRelease Reconciliation

```bash
# Annotate the HelmRelease to force reconciliation
kubectl annotate helmrelease ingress-nginx -n ingress-nginx reconcile.fluxcd.io/requestedAt="$(date +%s)" --overwrite

# Or use flux CLI
flux reconcile helmrelease ingress-nginx -n ingress-nginx
```

### Step 4: Restart Pods

```bash
# Restart the deployment
kubectl rollout restart deployment ingress-nginx-controller -n ingress-nginx

# Watch the rollout
kubectl rollout status deployment ingress-nginx-controller -n ingress-nginx
```

## Verification Steps

After applying changes, verify everything is working:

### 1. Check Pod Status

```bash
kubectl get pods -n ingress-nginx
```

All pods should be in `Running` state.

### 2. Check Pod Logs

```bash
# Check if Lua plugin is loaded (look for any errors)
kubectl logs -n ingress-nginx -l app.kubernetes.io/component=controller --tail=50
```

### 3. Verify ConfigMap is Mounted

```bash
# Check if the Lua file is in the pod
kubectl exec -n ingress-nginx deployment/ingress-nginx-controller -- ls -la /etc/nginx/lua/plugins/
```

You should see `redirect-404.lua` file.

### 4. Check Nginx Configuration

```bash
# Check if the Lua configuration is in nginx.conf
kubectl exec -n ingress-nginx deployment/ingress-nginx-controller -- cat /etc/nginx/nginx.conf | grep -A 10 "lua"
```

### 5. Test the 404 Redirect

```bash
# Test from your local machine
curl -I http://app.local/notfound

# Expected output:
# HTTP/1.1 302 Moved Temporarily
# Location: https://www.google.com
```

## Troubleshooting

### If pods don't restart automatically:

```bash
# Check HelmRelease status
kubectl describe helmrelease ingress-nginx -n ingress-nginx

# Check for errors in Flux logs
kubectl logs -n flux-system -l app=helm-controller --tail=50
```

### If Lua plugin is not working:

1. **Check if Lua is enabled in ingress-nginx:**
   ```bash
   kubectl exec -n ingress-nginx deployment/ingress-nginx-controller -- nginx -V 2>&1 | grep lua
   ```

2. **Check nginx configuration for syntax errors:**
   ```bash
   kubectl exec -n ingress-nginx deployment/ingress-nginx-controller -- nginx -t
   ```

3. **Check pod logs for Lua errors:**
   ```bash
   kubectl logs -n ingress-nginx -l app.kubernetes.io/component=controller | grep -i lua
   ```

### Force complete restart:

```bash
# Scale down to 0
kubectl scale deployment ingress-nginx-controller -n ingress-nginx --replicas=0

# Wait a few seconds
sleep 5

# Scale back up
kubectl scale deployment ingress-nginx-controller -n ingress-nginx --replicas=1

# Or use the number of replicas you have configured
```

## Quick Reference Commands

```bash
# Check Flux sync status
flux get kustomizations

# Force reconcile infrastructure
flux reconcile kustomization infrastructure

# Check ingress-nginx pods
kubectl get pods -n ingress-nginx

# Restart ingress-nginx
kubectl rollout restart deployment ingress-nginx-controller -n ingress-nginx

# Watch pod restart
kubectl get pods -n ingress-nginx -w

# Check logs
kubectl logs -n ingress-nginx -l app.kubernetes.io/component=controller --tail=100 -f

# Test 404 redirect
curl -I http://app.local/notfound
```

