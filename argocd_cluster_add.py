import os
import subprocess
import json
import time
import tempfile

# Read environment variables
CLUSTER_NAME = os.getenv("CLUSTER_NAME")
CLUSTER_API_SERVER = os.getenv("CLUSTER_API_SERVER")
TARGET_KUBECONFIG = os.getenv("KUBECONFIG_PATH")  # Target cluster kubeconfig
ARGOCD_KUBECONFIG = os.getenv("ARGOCD_KUBECONFIG")  # Local ArgoCD cluster kubeconfig
ARGOCD_NAMESPACE = "argocd"

# Validate inputs
if not CLUSTER_NAME or not CLUSTER_API_SERVER or not TARGET_KUBECONFIG or not ARGOCD_KUBECONFIG:
    print("❌ ERROR: Please export CLUSTER_NAME, CLUSTER_API_SERVER, KUBECONFIG_PATH (target), and ARGOCD_KUBECONFIG (local ArgoCD) before running the script.")
    exit(1)

# Function to run shell commands
def run_command(cmd):
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"❌ ERROR: {e.stderr}")
        exit(1)

print(f"🚀 Configuring target cluster: {CLUSTER_NAME}")

# Set kubeconfig to target cluster
os.environ["KUBECONFIG"] = TARGET_KUBECONFIG

# Function to apply YAML using a temporary file
def apply_yaml(yaml_content):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".yml") as tmpfile:
        tmpfile.write(yaml_content.encode())
        tmpfile_path = tmpfile.name

    run_command(f"kubectl apply -f {tmpfile_path}")
    os.remove(tmpfile_path)  # Cleanup temp file

# Create Service Account
sa_yaml = """\
apiVersion: v1
kind: ServiceAccount
metadata:
  name: argocd-manager
  namespace: kube-system
"""
apply_yaml(sa_yaml)

# Create ClusterRoleBinding
rb_yaml = """\
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: argocd-manager-rolebinding
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: cluster-admin
subjects:
  - kind: ServiceAccount
    name: argocd-manager
    namespace: kube-system
"""
apply_yaml(rb_yaml)

# Wait for resources to be created
time.sleep(5)

# Get Service Account Token from target cluster
TOKEN = run_command("kubectl create token argocd-manager --namespace=kube-system")

# Switch kubeconfig to local ArgoCD cluster
os.environ["KUBECONFIG"] = ARGOCD_KUBECONFIG
print(f"🔄 Switched to ArgoCD cluster to register {CLUSTER_NAME}")

# Create Kubernetes Secret for ArgoCD
secret_yaml = f"""\
apiVersion: v1
kind: Secret
metadata:
  name: {CLUSTER_NAME}
  namespace: {ARGOCD_NAMESPACE}
  labels:
    argocd.argoproj.io/secret-type: cluster
    environment: {CLUSTER_NAME}
type: Opaque
stringData:
  name: {CLUSTER_NAME}
  server: "{CLUSTER_API_SERVER}"
  config: |
    {{
      "bearerToken": "{TOKEN}",
      "tlsClientConfig": {{
          "insecure": true
      }}
    }}
"""
apply_yaml(secret_yaml)

print(f"✅ Cluster {CLUSTER_NAME} has been successfully added to ArgoCD!")

# List clusters in ArgoCD
# run_command("argocd cluster list")
