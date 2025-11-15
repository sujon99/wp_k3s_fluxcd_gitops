# WordPress on k3s with FluxCD GitOps

This project deploys a WordPress application on k3s using FluxCD for GitOps automation. The setup includes MySQL database, MetalLB for load balancing, and NGINX Ingress Controller.

## Architecture

- **k3s**: Lightweight Kubernetes distribution
- **FluxCD**: GitOps tool for continuous deployment
- **MySQL 8.0**: Database backend with automatic user provisioning
- **WordPress**: Latest WordPress container image
- **MetalLB**: Load balancer for bare-metal k3s clusters
- **NGINX Ingress**: Ingress controller for routing traffic
- **SOPS + Age**: Encrypted secrets management

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
│   ├── metallb/                  # MetalLB load balancer
│   ├── ingress-nginx/            # NGINX Ingress Controller
│   └── helmrepositories/         # Helm repository definitions
└── flux-system/                  # FluxCD configuration
    ├── gotk-sync.yaml           # Git sync configuration
    └── sops.yaml                 # SOPS decryption secret
```

## Key Features

- **Automatic MySQL User Provisioning**: The MySQL deployment includes a `postStart` lifecycle hook that automatically creates the WordPress database user and grants necessary privileges, eliminating the need for manual database setup.
- **Encrypted Secrets**: All sensitive data is encrypted using SOPS with Age encryption.
- **GitOps Workflow**: All changes are managed through Git, with FluxCD automatically syncing and applying updates.

## Prerequisites

- k3s installed and running
- kubectl configured
- flux CLI installed
- sops installed
- age installed
- GitHub account (for GitOps repository)

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

### 3. Generate Age Key for SOPS

```bash
age-keygen -o age.agekey
```

Copy the public key (starts with `age1...`) and private key content.

### 4. Configure SOPS

Update `.sops.yaml` with age public key:

```yaml
creation_rules:
  - path_regex: .*secret.*\.yaml$
    encrypted_regex: ^(data|stringData)$
    age: age1PUBLIC_KEY_HERE
```

### 5. Encrypt Secrets

Create unencrypted secret files first, then encrypt them:

**MySQL Secret** (`clusters/default/apps/mysql/secret.yaml`):
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: mysql-secret
  namespace: mysql
type: Opaque
stringData:
  MYSQL_ROOT_PASSWORD: rootpassword123
  MYSQL_DATABASE: wordpress
  MYSQL_USER: wordpress
  MYSQL_PASSWORD: wordpress123
```

**WordPress Secret** (`clusters/default/apps/wordpress/secret.yaml`):
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: wordpress-db-secret
  namespace: wordpress
type: Opaque
stringData:
  MYSQL_DATABASE: wordpress
  MYSQL_USER: wordpress
  MYSQL_PASSWORD: wordpress123
```

Encrypt both secrets:
```bash
sops -e -i clusters/default/apps/mysql/secret.yaml
sops -e -i clusters/default/apps/wordpress/secret.yaml
```

### 6. Update FluxCD Configuration

Update `clusters/default/flux-system/gotk-sync.yaml` with GitHub repository:

```yaml
url: https://github.com/...
```

Update `clusters/default/flux-system/sops-decryption.yaml` with age private key:

```yaml
stringData:
  age.agekey: |
    # Paste private key from age.agekey file here
```

### 7. Update MetalLB IP Pool

Edit `clusters/default/infrastructure/metallb/ipaddresspool.yaml` and set IP range matching with network:

```yaml
addresses:
- 192.168.1.240-192.168.1.250  # Change to network range
```

### 8. Push to GitHub

```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/....
git push -u origin main
```

### 9. Bootstrap FluxCD

```bash
flux bootstrap github \
  --owner=USERNAME \
  --repository=REPO \
  --branch=main \
  --path=./clusters/default \
  --personal
```

### 10. Configure /etc/hosts

Add to `/etc/hosts` (or `C:\Windows\System32\drivers\etc\hosts` on Windows):

```
<INGRESS_IP> app.local
```

Get ingress IP:
```bash
kubectl get svc -n ingress-nginx ingress-nginx-controller
```

### 11. Verify Deployment

```bash
# Check FluxCD sync
flux get kustomizations

# Check pods
kubectl get pods -A

# Check ingress
kubectl get ingress -n wordpress
```

### 12. Access WordPress

Open browser: `http://app.local`

## How It Works

### MySQL Automatic User Provisioning

The MySQL deployment includes a `postStart` lifecycle hook that automatically:
1. Waits for MySQL to be ready (using `mysqladmin ping`)
2. Creates the WordPress database user if it doesn't exist
3. Grants all privileges on the WordPress database to the user
4. Flushes privileges to apply changes

This eliminates the need for manual database initialization or init containers. The lifecycle hook runs automatically after the MySQL container starts.

### Database Connection

WordPress connects to MySQL using the Kubernetes service DNS name:
- Service: `mysql.mysql.svc.cluster.local`
- Port: `3306`
- Database credentials are provided via encrypted secrets

## Troubleshooting

### Check FluxCD Status

```bash
# View all kustomizations
flux get kustomizations

# Check sync status
flux get kustomizations -A

# Force reconciliation
flux reconcile kustomization flux-system
flux reconcile kustomization infrastructure
flux reconcile kustomization apps
```

### Check Pod Status

```bash
# View all pods
kubectl get pods -A

# Check MySQL pod logs
kubectl logs -n mysql deployment/mysql

# Check WordPress pod logs
kubectl logs -n wordpress deployment/wordpress

# Describe pod for events
kubectl describe pod -n mysql <pod-name>
kubectl describe pod -n wordpress <pod-name>
```

### Check Services and Ingress

```bash
# Check services
kubectl get svc -A

# Check ingress
kubectl get ingress -A
kubectl describe ingress -n wordpress wordpress

# Check MetalLB
kubectl get svc -n metallb-system
kubectl get ipaddresspool -n metallb-system
```

### Check Secrets

```bash
# Verify secrets are decrypted (should show plain text)
kubectl get secret -n mysql mysql-secret -o yaml
kubectl get secret -n wordpress wordpress-db-secret -o yaml
```

### Common Issues

1. **MySQL pod not starting**: Check if secrets are properly decrypted
   ```bash
   kubectl get secret -n mysql mysql-secret
   ```

2. **WordPress can't connect to MySQL**: Verify service DNS and credentials
   ```bash
   kubectl exec -n wordpress deployment/wordpress -- nslookup mysql.mysql.svc.cluster.local
   ```

3. **Ingress not working**: Check MetalLB IP assignment and ingress controller
   ```bash
   kubectl get svc -n ingress-nginx ingress-nginx-controller
   kubectl get ingress -n wordpress
   ```

4. **FluxCD not syncing**: Check Git repository access and reconciliation
   ```bash
   kubectl logs -n flux-system -l app=source-controller
   flux reconcile source git flux-system
   ```

5. **SOPS decryption failing**: Verify age key in flux-system namespace
   ```bash
   kubectl get secret -n flux-system sops-age -o yaml
   ```

### Debug Commands

```bash
# Get all resources in namespaces
kubectl get all -n mysql
kubectl get all -n wordpress

# Check events
kubectl get events -n mysql --sort-by='.lastTimestamp'
kubectl get events -n wordpress --sort-by='.lastTimestamp'

# Test MySQL connection from WordPress pod
kubectl exec -n wordpress deployment/wordpress -- \
  sh -c 'nc -zv mysql.mysql.svc.cluster.local 3306'
```

## Maintenance

### Updating Secrets

1. Decrypt the secret file:
   ```bash
   sops -d clusters/default/apps/mysql/secret.yaml > /tmp/mysql-secret.yaml
   ```

2. Edit the decrypted file:
   ```bash
   # Edit /tmp/mysql-secret.yaml with changes
   ```

3. Re-encrypt and replace:
   ```bash
   sops -e /tmp/mysql-secret.yaml > clusters/default/apps/mysql/secret.yaml
   rm /tmp/mysql-secret.yaml
   ```

4. Commit and push changes:
   ```bash
   git add clusters/default/apps/mysql/secret.yaml
   git commit -m "Update MySQL secret"
   git push
   ```

5. FluxCD will automatically sync and apply the changes.

### Updating Application Images

Edit the deployment YAML files and update the image tag:
- `clusters/default/apps/mysql/deployment.yaml` - Update `image: mysql:8.0`
- `clusters/default/apps/wordpress/deployment.yaml` - Update `image: wordpress:latest`

Commit and push, FluxCD will handle the rollout.

### Scaling Applications

To scale WordPress, update the `replicas` field in `clusters/default/apps/wordpress/deployment.yaml`:
```yaml
spec:
  replicas: 3  # Change from 1 to desired number
```

**Note**: MySQL is currently configured with `replicas: 1`. For production, consider using a StatefulSet with persistent volumes and proper replication.

## Storage Considerations

Currently, both MySQL and WordPress use `emptyDir` volumes, which means:
- Data is ephemeral and will be lost when pods are deleted
- Suitable for development/testing only

For production deployments, consider:
- Using PersistentVolumes (PV) and PersistentVolumeClaims (PVC)
- Using a storage class appropriate for k3s setup (e.g., local-path-provisioner)
- Implementing proper backup strategies

## Security Notes

- Change default passwords in secrets before deploying to production
- Use strong, unique passwords for database credentials
- Keep the age private key secure and never commit it to the repository
- Regularly rotate secrets and keys
- Consider using external secret management solutions for production

## License

This is a learning/example project.

