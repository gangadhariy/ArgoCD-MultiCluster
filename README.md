## ArgoCD Multi-Cluster Management Script

This script automates the process of adding and removing Kubernetes clusters in ArgoCD. It handles service account creation, cluster role bindings, and secret management within ArgoCD.

---

## Prerequisites

Ensure you have the following installed:
- Python 3.x
- `kubectl` configured for both ArgoCD and the target cluster
- `argocd` CLI installed and authenticated
- Environment variables exported properly

---

## Environment Variables

Before running the script, set up the following environment variables:

```sh
export CLUSTER_API_SERVER="https://10.1.149.63:6443"
export ARGOCD_NAMESPACE="argocd"
export CLUSTER_NAME="production"
export LABEL="App1"
export ARGOCD_KUBECONFIG="/home/$USER/Desktop/skupper/argocd.config"
export TARGET_KUBECONFIG="/home/$USER/Desktop/skupper/master.config"
export ARGOCD_SERVER="localhost:8080"
```

### Explanation of Variables:
- **CLUSTER_API_SERVER** - API server URL of the target cluster.
- **ARGOCD_NAMESPACE** - The namespace where ArgoCD is installed.
- **CLUSTER_NAME** - The name of the cluster to be added/removed.
- **LABEL** - Label used for identifying the cluster in ArgoCD.
- **ARGOCD_KUBECONFIG** - Path to the kubeconfig file for the ArgoCD cluster.
- **TARGET_KUBECONFIG** - Path to the kubeconfig file for the target cluster.
- **ARGOCD_SERVER** - ArgoCD API server address.

---

## Setup and Execution

### 1. Export Environment Variables
For **Linux/macOS**, run:
```sh
source ./export.sh
```
For **Windows (PowerShell)**, run:
```powershell
./export.ps1
```

### 2. Run the Script
To **add** a cluster:
```sh
python argocd-clusteradd-rm.py add
```
To **remove** a cluster:
```sh
python argocd-clusteradd-rm.py remove
```

---

## Error Handling
- If the target cluster is unreachable or does not exist, the script will **only** remove the ArgoCD secret and skip service account and cluster role binding deletion.
- The script will safely handle cases where resources are already deleted or missing.

---

## Troubleshooting
- Run `kubectl get secrets -n argocd` to verify cluster secrets in ArgoCD.
- Run `argocd cluster list` to check registered clusters.
- If issues occur, ensure environment variables are correctly set and kubeconfigs are properly configured.

---

## License
MIT License

