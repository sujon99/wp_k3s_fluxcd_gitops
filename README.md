# WordPress on k3s with FluxCD GitOps

## Prerequisites

- k3s installed and running
- kubectl configured
- flux CLI installed
- sops installed
- age installed

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

Update `.sops.yaml` with your age public key:

```yaml
creation_rules:
  - path_regex: .*secret.*\.yaml$
    encrypted_regex: ^(data|stringData)$
    age: age1YOUR_PUBLIC_KEY_HERE
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

Update `clusters/default/flux-system/gotk-sync.yaml` with your GitHub repository:

```yaml
url: https://github.com/YOUR_USERNAME/YOUR_REPO
```

Update `clusters/default/flux-system/sops-decryption.yaml` with your age private key:

```yaml
stringData:
  age.agekey: |
    # Paste your private key from age.agekey file here
```

### 7. Update MetalLB IP Pool

Edit `clusters/default/infrastructure/metallb/ipaddresspool.yaml` and set IP range matching your network:

```yaml
addresses:
- 192.168.1.240-192.168.1.250  # Change to your network range
```

### 8. Push to GitHub

```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
git push -u origin main
```

### 9. Bootstrap FluxCD

```bash
flux bootstrap github \
  --owner=YOUR_USERNAME \
  --repository=YOUR_REPO \
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

## Troubleshooting

- Check FluxCD logs: `kubectl logs -n flux-system -l app=helm-controller`
- Check pod status: `kubectl get pods -A`
- Check MetalLB: `kubectl get svc -n metallb-system`
- Force reconciliation: `flux reconcile kustomization flux-system`

