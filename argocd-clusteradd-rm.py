import os
import subprocess
import sys
import json
import time
import tempfile

# Read environment variables
CLUSTER_NAME = os.getenv("CLUSTER_NAME")
LABEL        = os.getenv("LABEL")
CLUSTER_API_SERVER = os.getenv("CLUSTER_API_SERVER") # Target cluster server URL
TARGET_KUBECONFIG = os.getenv("TARGET_KUBECONFIG")  # Target cluster kubeconfig
ARGOCD_KUBECONFIG = os.getenv("ARGOCD_KUBECONFIG")  # Local ArgoCD cluster kubeconfig
ARGOCD_NAMESPACE = "argocd"

# Validate inputs
if not CLUSTER_NAME or not TARGET_KUBECONFIG or not ARGOCD_KUBECONFIG:
    print("❌ ERROR: Missing required environment variables!")
    exit(1)

def run_command(cmd):
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"❌ ERROR: {e.stderr.strip()}")
        exit(1)

def apply_yaml(yaml_content):
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".yml") as tmpfile:
            tmpfile.write(yaml_content.encode())
            tmpfile_path = tmpfile.name
        run_command(f"kubectl apply -f {tmpfile_path}")
    finally:
        if os.path.exists(tmpfile_path):
            os.remove(tmpfile_path)

def add_cluster():
    try:
        print(f"🚀 Registering cluster: {CLUSTER_NAME}")
        os.environ["KUBECONFIG"] = TARGET_KUBECONFIG

        print("🔧 Creating ServiceAccount...")
        sa_yaml = """
apiVersion: v1
kind: ServiceAccount
metadata:
  name: argocd-manager
  namespace: kube-system
"""
        apply_yaml(sa_yaml)
        print("✅ ServiceAccount created!")

        print("🔧 Creating ClusterRoleBinding...")
        rb_yaml = """
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
        print("✅ ClusterRoleBinding created!")

        time.sleep(5)
        print("🔑 Generating ServiceAccount token...")
        TOKEN = run_command("kubectl create token argocd-manager --namespace=kube-system")
        print("✅ Token created successfully!")

        os.environ["KUBECONFIG"] = ARGOCD_KUBECONFIG
        print("🔐 Creating ArgoCD Secret...")
        secret_yaml = f"""
apiVersion: v1
kind: Secret
metadata:
  name: {CLUSTER_NAME}
  namespace: {ARGOCD_NAMESPACE}
  labels:
    argocd.argoproj.io/secret-type: cluster
    environment: {LABEL}
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
        print("✅ ArgoCD Secret created!")
        print(f"✅ Cluster {CLUSTER_NAME} successfully added to ArgoCD! Run (argocd cluster list) to confirm.")
    except KeyboardInterrupt:
        print("\n❌ Operation canceled by user.")
        exit(1)

def remove_cluster():
    try:
        print(f"🚀 Removing cluster: {CLUSTER_NAME} from ArgoCD...")
        os.environ["KUBECONFIG"] = ARGOCD_KUBECONFIG
        print("🔄 Deleting cluster secret from ArgoCD...")
        try:
            run_command(f"kubectl delete secret {CLUSTER_NAME} -n {ARGOCD_NAMESPACE}")            
            print("✅ ArgoCD Secret deleted!")
        except:
            print(f"cluster {CLUSTER_NAME} not")

        os.environ["KUBECONFIG"] = TARGET_KUBECONFIG
        print("🗑️ Deleting ServiceAccount...")
        run_command("kubectl delete serviceaccount argocd-manager -n kube-system")
        print("✅ ServiceAccount deleted!")

        print("🗑️ Deleting ClusterRoleBinding...")
        run_command("kubectl delete clusterrolebinding argocd-manager-rolebinding")
        print("✅ ClusterRoleBinding deleted!")

        print(f"✅ Cluster {CLUSTER_NAME} successfully removed. Run (argocd cluster list) to confirm.")
    except KeyboardInterrupt:
        print("\n❌ Operation canceled by user.")
        exit(1)

if len(sys.argv) < 2:
    print("❌ ERROR: Specify 'add' or 'remove' as an argument.")
    exit(1)

action = sys.argv[1].lower()
if action == "add":
    add_cluster()
elif action == "remove":
    remove_cluster()
else:
    print("❌ ERROR: Invalid argument. Use 'add' or 'remove'.")
    exit(1)
