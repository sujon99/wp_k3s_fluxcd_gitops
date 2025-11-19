# WordPress on k3s with FluxCD GitOps

This project deploys a WordPress application on k3s using FluxCD for GitOps automation. The setup includes MySQL database, MetalLB for load balancing, NGINX Ingress Controller with custom Lua plugin for 404 redirects.

## Architecture

- **k3s**: Lightweight Kubernetes distribution
- **FluxCD**: GitOps tool for continuous deployment
- **MySQL 8.0**: Database backend with automatic user provisioning
- **WordPress**: Latest WordPress container image
- **MetalLB**: Load balancer for bare-metal k3s clusters
- **NGINX Ingress**: Ingress controller with custom Lua plugin
- **SOPS + Age**: Encrypted secrets management

## Key Features

- **Custom 404 Redirect**: Ingress-NGINX Lua plugin redirects all 404 responses to google.com
- **Automatic MySQL User Provisioning**: MySQL deployment includes lifecycle hooks for automatic database setup
- **Encrypted Secrets**: All sensitive data encrypted using SOPS with Age encryption
- **GitOps Workflow**: All changes managed through Git with FluxCD auto-sync

## Project Structure

```
clusters/default/
├── apps/
│   ├── mysql/
│   │   ├── deployment.yaml      # MySQL deployment with lifecycle hooks
│   │   ├── service.yaml          # MySQL ClusterIP service
│   │   ├── secret.yaml          # Encrypted MySQL credentials
│   │   ├── namespace.yaml        # MySQL namespace
│   │   └── kustomization.yaml
│   └── wordpress/
│       ├── deployment.yaml       # WordPress deployment
│       ├── service.yaml          # WordPress service
│       ├── ingress.yaml          # Ingress configuration
│       ├── secret.yaml           # Encrypted WordPress DB credentials
│       ├── namespace.yaml        # WordPress namespace
│       └── kustomization.yaml
├── infrastructure/
│   ├── metallb/
│   │   └── config/          # MetalLB IP pool configuration
│   ├── ingress-nginx/
│   │   ├── lua-redirect-plugin.yaml  # Custom Lua plugin for 404 redirects
│   │   ├── default-backend.yaml
│   │   └── helmrelease.yaml
│   └── helmrepositories/
└── flux-system/
    ├── gotk-sync.yaml
    └── sops.yaml
```

## Prerequisites

- k3s installed and running
- kubectl configured
- flux CLI installed
- sops and age installed (for secret encryption)
- GitHub account with repository

## Setup Steps

### 1. Install k3s

```bash
curl -sfL https://get.k3s.io | sh -
sudo kubectl get nodes
```

### 2. Install Flux CLI

```bash
curl -s https://fluxcd.io/install.sh | sudo bash
```

### 3. Configure SOPS Age Secret

**IMPORTANT**: The Age private key is NOT stored in Git for security reasons. You must create it manually.

#### Generate Age Key Pair (if you don't have one):

```bash
# Install age
# Linux: apt-get install age or pacman -S age
# macOS: brew install age
# Windows: scoop install age or download from https://github.com/FiloSottile/age/releases

# Generate age key pair
age-keygen -o age.key

# Display public key (add this to .sops.yaml)
age-keygen -y age.key
```

#### Create the SOPS Secret in Kubernetes:

```bash
# Create flux-system namespace first
kubectl create namespace flux-system

# Create the sops-age secret from your age private key file
kubectl create secret generic sops-age \
  --namespace=flux-system \
  --from-file=age.agekey=age.key

# Verify the secret was created
kubectl get secret sops-age -n flux-system
```

**Note**: Keep your `age.key` file secure and do NOT commit it to Git.

### 4. Update Configuration Files

**Update Git Repository URL:**
Edit `clusters/default/flux-system/gotk-sync.yaml`:
```yaml
url: https://github.com/sujon99/wp_k3s_fluxcd_gitops
```

**Update MetalLB IP Pool:**
Edit `clusters/default/infrastructure/metallb/config/ipaddresspool.yaml`:
```yaml
addresses:
- 172.18.60.200-172.18.60.220  # Change to your network range
```

### 5. Push to GitHub

```bash
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/sujon99/wp_k3s_fluxcd_gitops.git
git push -u origin main
```

### 6. Bootstrap FluxCD

```bash
# Create flux-system namespace first
kubectl create namespace flux-system

# Bootstrap FluxCD
flux bootstrap github \
  --owner=sujon99 \
  --repository=wp_k3s_fluxcd_gitops \
  --branch=main \
  --path=./clusters/default \
  --personal
```

### 7. Apply GitRepository and Kustomization

If bootstrap fails to create GitRepository/Kustomization:

```bash
kubectl apply -f clusters/default/flux-system/gotk-sync.yaml
flux reconcile source git flux-system
flux reconcile kustomization flux-system
```

### 8. Deploy Infrastructure

```bash
# Deploy infrastructure (MetalLB, Ingress-NGINX)
kubectl apply -k clusters/default/infrastructure/

# Wait for ingress-nginx to be ready
kubectl wait --for=condition=ready pod -l app.kubernetes.io/component=controller -n ingress-nginx --timeout=300s
```

### 9. Apply MetalLB IP Pool

```bash
# Apply MetalLB IP pool configuration
kubectl apply -f clusters/default/infrastructure/metallb/config/ipaddresspool.yaml

# Verify IP pool is created
kubectl get ipaddresspool -n metallb-system
kubectl get l2advertisement -n metallb-system
```

### 10. Deploy Applications

```bash
# Deploy applications (MySQL, WordPress)
kubectl apply -k clusters/default/apps/

# Or let FluxCD handle it
flux reconcile kustomization flux-system
```

### 11. Get Ingress IP

```bash
kubectl get svc -n ingress-nginx ingress-nginx-controller
```

### 12. Configure /etc/hosts

Add to `/etc/hosts` (or `C:\Windows\System32\drivers\etc\hosts` on Windows):
```
<INGRESS_IP> app.local
```

### 13. Verify Deployment

```bash
# Check all pods
kubectl get pods --all-namespaces

# Check ingress
kubectl get ingress --all-namespaces

# Test 404 redirect (should redirect to google.com)
curl -I http://app.local/notfound
```

## Custom 404 Redirect Feature

The ingress-nginx controller includes a custom Lua plugin that redirects all 404 (Not Found) responses to `https://www.google.com`.

**Configuration:**
- Lua plugin: `clusters/default/infrastructure/ingress-nginx/lua-redirect-plugin.yaml`
- Ingress-NGINX config: `clusters/default/infrastructure/ingress-nginx/helmrelease.yaml`

**Test:**
```bash
curl -I http://app.local/notfound
# Expected: HTTP/1.1 302 Moved Temporarily
#           Location: https://www.google.com
```

## Troubleshooting

### Check Pod Status

```bash
kubectl get pods --all-namespaces
kubectl logs -n mysql deployment/mysql
kubectl logs -n wordpress deployment/wordpress
kubectl logs -n ingress-nginx -l app.kubernetes.io/component=controller
```

### Check Services and Ingress

```bash
kubectl get svc --all-namespaces | grep LoadBalancer
kubectl get ingress --all-namespaces
kubectl describe ingress wordpress -n wordpress
```

### Check MetalLB

```bash
kubectl get ipaddresspool -n metallb-system
kubectl get l2advertisement -n metallb-system
```

### Check FluxCD Status

```bash
flux get kustomizations
flux reconcile source git flux-system
flux reconcile kustomization flux-system
```

### Common Issues

1. **LoadBalancer IP is pending**: Apply MetalLB IP pool configuration
   ```bash
   kubectl apply -f clusters/default/infrastructure/metallb/config/ipaddresspool.yaml
   ```

2. **Ingress validation webhook errors**: Wait for ingress-nginx to be fully ready before deploying applications

3. **Secrets not decrypted**: Verify SOPS age key in `clusters/default/flux-system/sops.yaml`

4. **404 redirect not working**: Check ingress-nginx pod logs for Lua errors
   ```bash
   kubectl logs -n ingress-nginx -l app.kubernetes.io/component=controller | grep -i lua
   ```

## Restarting Applications

```bash
# Restart specific deployment
kubectl rollout restart deployment ingress-nginx-controller -n ingress-nginx
kubectl rollout restart deployment wordpress -n wordpress
kubectl rollout restart deployment mysql -n mysql

# Restart all deployments in a namespace
kubectl rollout restart deployment -n ingress-nginx
```

## Accessing the Application

- **WordPress**: `http://app.local` (or `http://<INGRESS_IP>`)
- **Test 404 Redirect**: `http://app.local/notfound` (redirects to google.com)

## Backup and Restore

Both WordPress and MySQL PVCs are configured with backup annotations for Velero integration.

### Prerequisites

Install Velero in your cluster:

```bash
# Install Velero CLI
# Linux/macOS:
wget https://github.com/vmware-tanzu/velero/releases/latest/download/velero-linux-amd64.tar.gz
tar -xvf velero-linux-amd64.tar.gz
sudo mv velero-linux-amd64/velero /usr/local/bin/

# Windows: Download from https://github.com/vmware-tanzu/velero/releases

# Install Velero in cluster (example with local storage)
velero install \
  --provider aws \
  --plugins velero/velero-plugin-for-aws:v1.8.0 \
  --bucket velero-backups \
  --secret-file ./credentials-velero \
  --use-volume-snapshots=false \
  --backup-location-config region=minio,s3ForcePathStyle="true",s3Url=http://minio.velero.svc:9000
```

### Backup WordPress and MySQL

```bash
# Backup entire wordpress namespace (includes PVC)
velero backup create wordpress-backup --include-namespaces wordpress

# Backup entire mysql namespace (includes PVC)
velero backup create mysql-backup --include-namespaces mysql

# Backup both namespaces together
velero backup create full-backup --include-namespaces wordpress,mysql

# Check backup status
velero backup describe wordpress-backup
velero backup get
```

### Restore from Backup

```bash
# Restore WordPress
velero restore create --from-backup wordpress-backup

# Restore MySQL
velero restore create --from-backup mysql-backup

# Restore full backup
velero restore create --from-backup full-backup

# Check restore status
velero restore get
velero restore describe <restore-name>
```

### Manual PVC Backup (Alternative)

If not using Velero, manually backup PVC data:

```bash
# Backup WordPress PVC
kubectl exec -n wordpress deployment/wordpress -- tar czf - /var/www/html > wordpress-backup.tar.gz

# Backup MySQL data (requires shell access to pod)
kubectl exec -n mysql statefulset/mysql -- mysqldump -uroot -p$MYSQL_ROOT_PASSWORD --all-databases > mysql-backup.sql

# Restore WordPress
kubectl exec -n wordpress deployment/wordpress -i -- tar xzf - -C /var/www/html < wordpress-backup.tar.gz

# Restore MySQL
kubectl exec -n mysql statefulset/mysql -i -- mysql -uroot -p$MYSQL_ROOT_PASSWORD < mysql-backup.sql
```

## License

This is a learning/example project.
