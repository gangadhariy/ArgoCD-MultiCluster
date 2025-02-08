import os
import subprocess

# Read environment variables
CLUSTER_NAME = os.getenv("CLUSTER_NAME")  # Name of the cluster to remove
TARGET_KUBECONFIG = os.getenv("KUBECONFIG_PATH")  # Target cluster kubeconfig
ARGOCD_KUBECONFIG = os.getenv("ARGOCD_KUBECONFIG")  # Local ArgoCD cluster kubeconfig
ARGOCD_NAMESPACE = "argocd"

# Validate inputs
if not CLUSTER_NAME or not TARGET_KUBECONFIG or not ARGOCD_KUBECONFIG:
    print("❌ ERROR: Please export CLUSTER_NAME, KUBECONFIG_PATH (target), and ARGOCD_KUBECONFIG (local ArgoCD) before running the script.")
    exit(1)

# Function to run shell commands
def run_command(cmd):
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"❌ ERROR: {e.stderr}")
        exit(1)

print(f"🚀 Removing cluster: {CLUSTER_NAME} from ArgoCD...")

# Step 1: Delete Secret from ArgoCD
os.environ["KUBECONFIG"] = ARGOCD_KUBECONFIG
print(f"🔄 Deleting cluster secret from ArgoCD: {CLUSTER_NAME}")
run_command(f"kubectl delete secret {CLUSTER_NAME} -n {ARGOCD_NAMESPACE}")

# Step 2: Switch to Target Cluster to clean up RBAC
os.environ["KUBECONFIG"] = TARGET_KUBECONFIG
print(f"🔄 Removing Service Account and ClusterRoleBinding from target cluster: {CLUSTER_NAME}")

# Delete Service Account
run_command("kubectl delete serviceaccount argocd-manager -n kube-system")

# Delete ClusterRoleBinding
run_command("kubectl delete clusterrolebinding argocd-manager-rolebinding")

print(f"✅ Cluster {CLUSTER_NAME} has been successfully removed from ArgoCD and the target cluster!")

# Step 3: Verify the Cluster is Removed
os.environ["KUBECONFIG"] = ARGOCD_KUBECONFIG
print("🔎 Verifying removal from ArgoCD...")

print("🎉 Cluster removal process completed!")
