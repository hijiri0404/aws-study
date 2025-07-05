# CKS Practice Exam 01 - 100問

## 📋 試験概要

**制限時間**: 120分  
**問題数**: 100問  
**合格点**: 67点以上  
**形式**: 実技試験（kubectl操作）

## 🎯 ドメイン別配点

- Cluster Setup (10%) - 10問
- Cluster Hardening (15%) - 15問  
- System Hardening (15%) - 15問
- Minimize Microservice Vulnerabilities (20%) - 20問
- Supply Chain Security (20%) - 20問
- Monitoring, Logging and Runtime Security (20%) - 20問

---

## 🏗️ Domain 1: Cluster Setup (10問)

### 問題1 (2点)
etcdデータベースの暗号化を有効にしてください。
- 暗号化設定ファイル: `/etc/kubernetes/encryption-config.yaml`
- 使用する暗号化方式: `aescbc`
- API Serverを再起動し、既存のsecretを再暗号化してください

**解答例:**
```bash
# 1. 暗号化設定ファイル作成
sudo cat > /etc/kubernetes/encryption-config.yaml << EOF
apiVersion: apiserver.config.k8s.io/v1
kind: EncryptionConfiguration
resources:
- resources:
  - secrets
  providers:
  - aescbc:
      keys:
      - name: key1
        secret: $(head -c 32 /dev/urandom | base64)
  - identity: {}
EOF

# 2. API Server設定更新
sudo vim /etc/kubernetes/manifests/kube-apiserver.yaml
# --encryption-provider-config=/etc/kubernetes/encryption-config.yaml を追加

# 3. 既存secretの再暗号化
kubectl get secrets --all-namespaces -o json | kubectl replace -f -
```

### 問題2 (2点)
kubeletのセキュリティ設定を強化してください。
- 匿名アクセスを無効化
- ReadOnlyPortを無効化
- Webhook認証を有効化

**解答例:**
```bash
sudo vim /var/lib/kubelet/config.yaml
```
```yaml
authentication:
  anonymous:
    enabled: false
  webhook:
    enabled: true
authorization:
  mode: Webhook
readOnlyPort: 0
```

### 問題3 (2点)
API Serverへの匿名アクセスを完全に無効化してください。

**解答例:**
```bash
sudo vim /etc/kubernetes/manifests/kube-apiserver.yaml
# --anonymous-auth=false を追加
```

### 問題4 (2点)
TLS証明書の有効期限を確認し、kubelet証明書の自動ローテーションを有効化してください。

**解答例:**
```bash
# 証明書の確認
sudo openssl x509 -in /etc/kubernetes/pki/apiserver.crt -text -noout | grep "Not After"

# kubelet設定更新
sudo vim /var/lib/kubelet/config.yaml
# rotateCertificates: true を追加
```

### 問題5 (2点)
Control Planeコンポーネントが適切なポートで動作していることを確認し、不要なポートを閉じてください。

**解答例:**
```bash
# ポートの確認
sudo netstat -tlnp | grep -E "(6443|2379|10250)"

# firewall設定
sudo ufw deny 10255  # kubelet read-only port
```

### 問題6 (1点)
API Serverの監査ログを有効化し、セキュリティイベントを記録してください。
- 監査ポリシーファイル: `/etc/kubernetes/audit-policy.yaml`
- ログファイル: `/var/log/kubernetes/audit.log`

**解答例:**
```bash
# 1. 監査ポリシー作成
sudo cat > /etc/kubernetes/audit-policy.yaml << EOF
apiVersion: audit.k8s.io/v1
kind: Policy
rules:
- level: Metadata
  resources:
  - group: ""
    resources: ["secrets", "configmaps"]
- level: Request
  resources:
  - group: "rbac.authorization.k8s.io"
    resources: ["roles", "rolebindings"]
EOF

# 2. API Server設定更新
sudo vim /etc/kubernetes/manifests/kube-apiserver.yaml
# 以下を追加:
# --audit-log-path=/var/log/kubernetes/audit.log
# --audit-policy-file=/etc/kubernetes/audit-policy.yaml
```

### 問題7 (1点)
kubeletのセキュリティ設定を強化してください。
- Read-only port無効化
- Anonymous認証無効化

**解答例:**
```bash
# 1. kubelet設定ファイル編集
sudo vim /var/lib/kubelet/config.yaml

# 以下を追加/変更:
# readOnlyPort: 0
# authentication:
#   anonymous:
#     enabled: false

# 2. kubelet再起動
sudo systemctl restart kubelet
```

### 問題8 (1点)
etcdデータベースのバックアップを作成してください。
- バックアップファイル: `/opt/etcd-backup.db`

**解答例:**
```bash
# etcdバックアップ作成
ETCDCTL_API=3 etcdctl snapshot save /opt/etcd-backup.db \
  --endpoints=https://127.0.0.1:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key

# バックアップ確認
ETCDCTL_API=3 etcdctl snapshot status /opt/etcd-backup.db
```

### 問題9 (1点)
Control Planeコンポーネントの証明書有効期限を確認し、期限切れ前の証明書を更新してください。

**解答例:**
```bash
# 1. 証明書有効期限確認
sudo kubeadm certs check-expiration

# 2. 期限切れ前証明書の更新
sudo kubeadm certs renew all

# 3. Control Plane再起動
sudo systemctl restart kubelet
```

### 問題10 (1点)
API Serverのアドミッションコントローラーを設定し、以下を有効化してください：
- NodeRestriction
- PodSecurityPolicy
- ResourceQuota

**解答例:**
```bash
# API Server設定更新（/etc/kubernetes/manifests/kube-apiserver.yaml）
# --enable-admission-plugins に以下を追加:
# NodeRestriction,PodSecurityPolicy,ResourceQuota

# API Server再起動確認
kubectl get pods -n kube-system | grep kube-apiserver
```

---

## 🔒 Domain 2: Cluster Hardening (15問)

### 問題6 (3点)
`restricted`名前空間を作成し、以下のRBAC設定を実装してください。
- Service Account: `restricted-sa`
- Role: podの読み取り専用権限
- 他のリソースへのアクセスは拒否

**解答例:**
```bash
kubectl create namespace restricted

cat << EOF | kubectl apply -f -
apiVersion: v1
kind: ServiceAccount
metadata:
  name: restricted-sa
  namespace: restricted
---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  namespace: restricted
  name: pod-reader
rules:
- apiGroups: [""]
  resources: ["pods"]
  verbs: ["get", "list", "watch"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: read-pods
  namespace: restricted
subjects:
- kind: ServiceAccount
  name: restricted-sa
  namespace: restricted
roleRef:
  kind: Role
  name: pod-reader
  apiGroup: rbac.authorization.k8s.io
EOF
```

### 問題7 (3点)
Network Policyを作成し、以下の通信制御を実装してください。
- `production`名前空間内のPodからのIngressトラフィックのみ許可
- Egressは`kube-system`名前空間のDNSのみ許可

**解答例:**
```bash
cat << EOF | kubectl apply -f -
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: production-network-policy
  namespace: production
spec:
  podSelector: {}
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: production
  egress:
  - to:
    - namespaceSelector:
        matchLabels:
          name: kube-system
    - podSelector:
        matchLabels:
          k8s-app: kube-dns
    ports:
    - protocol: UDP
      port: 53
EOF
```

### 問題8 (3点)
デフォルトのService Accountに対するトークンの自動マウントを無効化してください。

**解答例:**
```bash
kubectl patch serviceaccount default -p '{"automountServiceAccountToken": false}'
```

### 問題9 (3点)
ClusterRoleBindingを確認し、`system:anonymous`や`system:unauthenticated`への権限付与を削除してください。

**解答例:**
```bash
# 危険なBindingの確認
kubectl get clusterrolebinding -o wide | grep -E "(system:anonymous|system:unauthenticated)"

# 削除（該当するものがあれば）
kubectl delete clusterrolebinding system:anonymous
```

### 問題10 (3点)
Admission Controllerを設定し、SecurityContextの設定を強制してください。
- `runAsNonRoot: true`
- `allowPrivilegeEscalation: false`

**解答例:**
```bash
# Pod Security Standardsを使用
kubectl label namespace default pod-security.kubernetes.io/enforce=restricted
```

### 問題11 (2点)
ClusterRole `secret-reader` を作成し、`secrets` リソースに対して `get`, `list` 権限のみを付与してください。

**解答例:**
```bash
kubectl create clusterrole secret-reader --verb=get,list --resource=secrets
```

### 問題12 (2点)
`security-team` Service Accountを作成し、先ほど作成したClusterRoleをバインドしてください。

**解答例:**
```bash
kubectl create serviceaccount security-team
kubectl create clusterrolebinding security-team-binding \
  --clusterrole=secret-reader \
  --serviceaccount=default:security-team
```

### 問題13 (2点)
Network Policyで、`database` namespace内のPodへの通信を `app-tier` labelを持つPodからのみ許可してください。

**解答例:**
```bash
cat << EOF | kubectl apply -f -
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: database-access-policy
  namespace: database
spec:
  podSelector: {}
  policyTypes:
  - Ingress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          tier: app
    ports:
    - protocol: TCP
      port: 5432
EOF
```

### 問題14 (2点)
PodSecurityPolicyを作成し、特権コンテナを禁止してください。
- privileged: false
- allowPrivilegeEscalation: false

**解答例:**
```bash
cat << EOF | kubectl apply -f -
apiVersion: policy/v1beta1
kind: PodSecurityPolicy
metadata:
  name: restricted-psp
spec:
  privileged: false
  allowPrivilegeEscalation: false
  runAsUser:
    rule: 'MustRunAsNonRoot'
  seLinux:
    rule: 'RunAsAny'
  volumes:
  - 'configMap'
  - 'emptyDir'
  - 'projected'
  - 'secret'
  - 'downwardAPI'
  - 'persistentVolumeClaim'
EOF
```

### 問題15 (2点)
ImagePolicyWebhook AdmissionControllerを設定し、許可されたレジストリからのイメージのみを許可してください。

**解答例:**
```bash
# /etc/kubernetes/imagepolicy.json
cat << EOF | sudo tee /etc/kubernetes/imagepolicy.json
{
  "imagePolicy": {
    "kubeConfigFile": "/etc/kubernetes/admission_webhook.kubeconfig",
    "allowTTL": 50,
    "denyTTL": 50,
    "retryBackoff": 500,
    "defaultAllow": false
  }
}
EOF

# API Server設定に追加
# --enable-admission-plugins=ImagePolicyWebhook
# --admission-control-config-file=/etc/kubernetes/imagepolicy.json
```

### 問題16 (1点)
API Server匿名アクセスのロールバインディングを確認し、不要なものを削除してください。

**解答例:**
```bash
# 匿名アクセス確認
kubectl get clusterrolebinding -o wide | grep system:anonymous

# 不要なバインディング削除
kubectl delete clusterrolebinding system:discovery
```

### 問題17 (1点)
Kubernetes Dashboardのアクセス制御を強化してください。
- admin権限ではなく、read-only権限を設定

**解答例:**
```bash
# read-only ServiceAccount作成
kubectl create serviceaccount dashboard-readonly -n kubernetes-dashboard

# ClusterRole作成
kubectl create clusterrole dashboard-readonly --verb=get,list,watch --resource=*.*

# ClusterRoleBinding作成
kubectl create clusterrolebinding dashboard-readonly-binding \
  --clusterrole=dashboard-readonly \
  --serviceaccount=kubernetes-dashboard:dashboard-readonly
```

### 問題18 (1点)
kubeletの認証設定を確認し、webhook認証を有効化してください。

**解答例:**
```bash
# kubelet設定ファイル編集
sudo vim /var/lib/kubelet/config.yaml

# 以下を追加:
# authentication:
#   webhook:
#     enabled: true
#   x509:
#     clientCAFile: /etc/kubernetes/pki/ca.crt

sudo systemctl restart kubelet
```

### 問題19 (1点)
Control Planeノードへのssh接続を制限し、特定のIPアドレスからのみアクセスを許可してください。

**解答例:**
```bash
# UFW設定
sudo ufw deny ssh
sudo ufw allow from 192.168.1.100 to any port 22

# または/etc/hosts.allow
echo "sshd: 192.168.1.100" | sudo tee -a /etc/hosts.allow
echo "sshd: ALL" | sudo tee -a /etc/hosts.deny
```

### 問題20 (1点)
APIサーバーの要求率制限（rate limiting）を設定してください。

**解答例:**
```bash
# API Server設定に以下を追加
# --max-requests-inflight=400
# --max-mutating-requests-inflight=200

# /etc/kubernetes/manifests/kube-apiserver.yaml を編集
```

---

## 🛡️ Domain 3: System Hardening (15問)

### 問題21 (3点)
AppArmorプロファイルを作成し、nginxコンテナに適用してください。
- プロファイル名: `k8s-nginx`
- `/etc/nginx/`への読み取りアクセスのみ許可
- システムファイルへの書き込みを拒否

**解答例:**
```bash
# AppArmorプロファイル作成
sudo cat > /etc/apparmor.d/k8s-nginx << EOF
#include <tunables/global>

/usr/sbin/nginx flags=(attach_disconnected,mediate_deleted) {
  #include <abstractions/base>
  #include <abstractions/nameservice>

  capability setuid,
  capability setgid,

  /usr/sbin/nginx mr,
  /etc/nginx/ r,
  /etc/nginx/** r,
  /var/log/nginx/ rw,
  /var/log/nginx/** rw,

  deny /etc/passwd w,
  deny /etc/shadow rwklx,
  deny /proc/sys/kernel/** wklx,
}
EOF

# プロファイル読み込み
sudo apparmor_parser -r /etc/apparmor.d/k8s-nginx

# Pod作成
cat << EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: nginx-apparmor
  annotations:
    container.apparmor.security.beta.kubernetes.io/nginx: localhost/k8s-nginx
spec:
  containers:
  - name: nginx
    image: nginx
EOF
```

### 問題22 (3点)
Seccompプロファイルを作成し、許可されたsyscallのみを実行できるようにしてください。

**解答例:**
```bash
# Seccompプロファイル作成
sudo mkdir -p /var/lib/kubelet/seccomp/profiles
sudo cat > /var/lib/kubelet/seccomp/profiles/minimal.json << EOF
{
  "defaultAction": "SCMP_ACT_ERRNO",
  "architectures": ["SCMP_ARCH_X86_64"],
  "syscalls": [
    {
      "names": [
        "accept4", "arch_prctl", "bind", "brk", "close", "connect",
        "dup2", "epoll_create1", "epoll_ctl", "epoll_wait", "exit",
        "exit_group", "fchown", "fcntl", "fstat", "futex", "getdents64",
        "getpid", "getuid", "listen", "mmap", "munmap", "nanosleep",
        "openat", "poll", "read", "rt_sigaction", "rt_sigprocmask",
        "rt_sigreturn", "sendto", "set_robust_list", "setgid",
        "setgroups", "setuid", "socket", "write"
      ],
      "action": "SCMP_ACT_ALLOW"
    }
  ]
}
EOF

# Pod作成
cat << EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: secure-pod
spec:
  securityContext:
    seccompProfile:
      type: Localhost
      localhostProfile: profiles/minimal.json
  containers:
  - name: app
    image: busybox
    command: ["sleep", "3600"]
EOF
```

### 問題23 (3点)
ノードのLinuxカーネルモジュールを確認し、不要なモジュールをブラックリストに追加してください。

**解答例:**
```bash
# 読み込み済みモジュール確認
lsmod

# 不要なモジュールをブラックリスト
sudo cat >> /etc/modprobe.d/blacklist-rare-modules.conf << EOF
blacklist dccp
blacklist sctp
blacklist rds
blacklist tipc
EOF
```

### 問題24 (3点)
ファイルシステムのマウントオプションを確認し、セキュリティを強化してください。

**解答例:**
```bash
# 現在のマウントオプション確認
mount | grep -E "(nosuid|nodev|noexec)"

# /tmp を secure にマウント
sudo mount -o remount,noexec,nosuid,nodev /tmp
```

### 問題25 (3点)
systemdサービスの設定を確認し、不要なサービスを無効化してください。

**解答例:**
```bash
# サービス一覧確認
systemctl list-unit-files --type=service | grep enabled

# 不要なサービス無効化
sudo systemctl disable bluetooth
sudo systemctl disable cups
sudo systemctl stop bluetooth
sudo systemctl stop cups
```

### 問題26 (2点)
カーネルパラメータを設定し、セキュリティを強化してください。
- IP転送無効化
- ICMP リダイレクト無効化

**解答例:**
```bash
# /etc/sysctl.conf に追加
cat << EOF | sudo tee -a /etc/sysctl.conf
net.ipv4.ip_forward = 0
net.ipv4.conf.all.accept_redirects = 0
net.ipv4.conf.default.accept_redirects = 0
net.ipv6.conf.all.accept_redirects = 0
net.ipv6.conf.default.accept_redirects = 0
EOF

# 適用
sudo sysctl -p
```

### 問題27 (2点)
ノードへのSSHアクセスを強化してください。
- Root ログイン無効化
- パスワード認証無効化

**解答例:**
```bash
# /etc/ssh/sshd_config 編集
sudo sed -i 's/#PermitRootLogin yes/PermitRootLogin no/' /etc/ssh/sshd_config
sudo sed -i 's/#PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config

# SSH再起動
sudo systemctl restart sshd
```

### 問題28 (2点)
ファイルの実行権限を制御するため、noexecオプションでマウントされた一時ディレクトリを作成してください。

**解答例:**
```bash
# 一時ディレクトリ作成
sudo mkdir /tmp/secure-temp

# noexecでマウント
sudo mount -t tmpfs -o noexec,nosuid,nodev tmpfs /tmp/secure-temp

# /etc/fstab に永続化
echo "tmpfs /tmp/secure-temp tmpfs noexec,nosuid,nodev 0 0" | sudo tee -a /etc/fstab
```

### 問題29 (2点)
auditdを設定し、ファイルアクセスを監視してください。
- `/etc/kubernetes/` ディレクトリの監視

**解答例:**
```bash
# audit ルール追加
sudo auditctl -w /etc/kubernetes -p war -k kubernetes-config

# 永続化（/etc/audit/rules.d/kubernetes.rules）
echo "-w /etc/kubernetes -p war -k kubernetes-config" | sudo tee /etc/audit/rules.d/kubernetes.rules

# auditd 再起動
sudo systemctl restart auditd
```

### 問題30 (2点)
不要なネットワークサービスを無効化してください。
- 使用していないポートの確認と無効化

**解答例:**
```bash
# ポート確認
sudo ss -tuln

# 不要なサービス確認・停止
sudo systemctl list-units --type=service | grep -E "(telnet|ftp|rsh)"
sudo systemctl disable telnet.socket
sudo systemctl stop telnet.socket
```

### 問題31 (1点)
ファイルシステムの権限を確認し、world-writableファイルを修正してください。

**解答例:**
```bash
# world-writableファイル検索
sudo find / -type f -perm -002 -exec ls -l {} \; 2>/dev/null

# 権限修正例
sudo chmod o-w /path/to/file
```

### 問題32 (1点)
SUID/SGIDビットが設定されたファイルを確認し、不要なものを修正してください。

**解答例:**
```bash
# SUID/SGIDファイル検索
sudo find / -type f \( -perm -4000 -o -perm -2000 \) -exec ls -l {} \; 2>/dev/null

# 不要なSUIDビット削除
sudo chmod u-s /path/to/file
```

### 問題33 (1点)
デフォルトのumaskを設定し、セキュアなファイル権限を確保してください。

**解答例:**
```bash
# システム全体のumask設定
echo "umask 022" | sudo tee -a /etc/profile

# ユーザー固有設定
echo "umask 077" >> ~/.bashrc
```

### 問題34 (1点)
ログファイルの権限を確認し、適切に設定してください。

**解答例:**
```bash
# ログディレクトリ権限確認
ls -la /var/log/

# 権限修正
sudo chmod 640 /var/log/syslog
sudo chown root:adm /var/log/syslog
```

### 問題35 (1点)
システムのタイムゾーンと時刻同期を確認し、NTPを設定してください。

**解答例:**
```bash
# 現在の時刻設定確認
timedatectl status

# NTP有効化
sudo timedatectl set-ntp true

# タイムゾーン設定
sudo timedatectl set-timezone Asia/Tokyo
```

---

## 🔍 Domain 4: Minimize Microservice Vulnerabilities (20問)

### 問題36 (4点)
Pod Security Standardsを使用して、`baseline`レベルのセキュリティを`development`名前空間に適用してください。

**解答例:**
```bash
kubectl create namespace development
kubectl label namespace development \
  pod-security.kubernetes.io/enforce=baseline \
  pod-security.kubernetes.io/audit=baseline \
  pod-security.kubernetes.io/warn=baseline
```

### 問題17 (4点)
OPA Gatekeeperを使用して、すべてのPodにリソース制限を強制するポリシーを作成してください。

**解答例:**
```bash
cat << EOF | kubectl apply -f -
apiVersion: templates.gatekeeper.sh/v1beta1
kind: ConstraintTemplate
metadata:
  name: resourcelimits
spec:
  crd:
    spec:
      names:
        kind: ResourceLimits
      validation:
        type: object
  targets:
    - target: admission.k8s.gatekeeper.sh
      rego: |
        package resourcelimits

        violation[{"msg": msg}] {
          container := input.review.object.spec.containers[_]
          not container.resources.limits.memory
          msg := "Container must have memory limits"
        }
        
        violation[{"msg": msg}] {
          container := input.review.object.spec.containers[_]
          not container.resources.limits.cpu
          msg := "Container must have CPU limits"
        }
---
apiVersion: constraints.gatekeeper.sh/v1beta1
kind: ResourceLimits
metadata:
  name: must-have-limits
spec:
  match:
    kinds:
      - apiGroups: [""]
        kinds: ["Pod"]
EOF
```

### 問題18 (4点)
Service Meshを使用して、mTLS通信を設定してください。（Istio使用）

**解答例:**
```bash
# Istio サイドカー注入有効化
kubectl label namespace production istio-injection=enabled

# PeerAuthentication設定
cat << EOF | kubectl apply -f -
apiVersion: security.istio.io/v1beta1
kind: PeerAuthentication
metadata:
  name: default
  namespace: production
spec:
  mtls:
    mode: STRICT
EOF
```

### 問題19 (4点)
実行時セキュリティを強化するため、読み取り専用ルートファイルシステムを使用するPodを作成してください。

**解答例:**
```bash
cat << EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: readonly-pod
spec:
  securityContext:
    runAsNonRoot: true
    runAsUser: 1000
    fsGroup: 2000
  containers:
  - name: app
    image: nginx
    securityContext:
      allowPrivilegeEscalation: false
      readOnlyRootFilesystem: true
      runAsNonRoot: true
      runAsUser: 1000
      capabilities:
        drop:
        - ALL
    volumeMounts:
    - name: tmp
      mountPath: /tmp
    - name: var-cache
      mountPath: /var/cache/nginx
    - name: var-run
      mountPath: /var/run
  volumes:
  - name: tmp
    emptyDir: {}
  - name: var-cache
    emptyDir: {}
  - name: var-run
    emptyDir: {}
EOF
```

### 問題20 (4点)
Podの特権を最小化するため、不要なLinux capabilityをすべて削除してください。

**解答例:**
```bash
cat << EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: minimal-privileges
spec:
  containers:
  - name: app
    image: busybox
    command: ["sleep", "3600"]
    securityContext:
      allowPrivilegeEscalation: false
      capabilities:
        drop:
        - ALL
      runAsNonRoot: true
      runAsUser: 1000
EOF
```

---

## 🔐 Domain 5: Supply Chain Security (20問)

### 問題21 (4点)
Trivyを使用してコンテナイメージの脆弱性スキャンを実行し、HIGH以上の脆弱性がないことを確認してください。

**解答例:**
```bash
# Trivyインストール
curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh | sh -s -- -b /usr/local/bin

# イメージスキャン
trivy image --severity HIGH,CRITICAL nginx:latest
trivy image --severity HIGH,CRITICAL --exit-code 1 nginx:latest
```

### 問題22 (4点)
プライベートレジストリからのイメージのみを許可するAdmission Controllerを設定してください。

**解答例:**
```bash
cat << EOF | kubectl apply -f -
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: restrict-image-registries
spec:
  validationFailureAction: enforce
  background: false
  rules:
  - name: check-registry
    match:
      any:
      - resources:
          kinds:
          - Pod
    validate:
      message: "Images must be from approved registries"
      pattern:
        spec:
          containers:
          - image: "registry.company.com/*"
EOF
```

### 問題23 (4点)
cosignを使用してコンテナイメージに署名し、署名検証を有効化してください。

**解答例:**
```bash
# cosignインストール
curl -O -L "https://github.com/sigstore/cosign/releases/latest/download/cosign-linux-amd64"
sudo mv cosign-linux-amd64 /usr/local/bin/cosign
sudo chmod +x /usr/local/bin/cosign

# キーペア生成
cosign generate-key-pair

# イメージ署名
cosign sign --key cosign.key registry.company.com/myapp:v1.0

# 署名検証ポリシー
cat << EOF | kubectl apply -f -
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: verify-image-signature
spec:
  validationFailureAction: enforce
  background: false
  rules:
  - name: verify-signature
    match:
      any:
      - resources:
          kinds:
          - Pod
    verifyImages:
    - imageReferences:
      - "registry.company.com/*"
      key: |-
        -----BEGIN PUBLIC KEY-----
        [公開鍵の内容]
        -----END PUBLIC KEY-----
EOF
```

### 問題24 (4点)
Binary Authorization を設定し、署名されたイメージのみのデプロイを許可してください。

**解答例:**
```bash
# Binary Authorization Policy
cat << EOF | kubectl apply -f -
apiVersion: v1
kind: ConfigMap
metadata:
  name: binary-authorization-policy
data:
  policy.yaml: |
    defaultAdmissionRule:
      requireAttestationsBy:
      - projects/PROJECT_ID/attestors/prod-attestor
      evaluationMode: REQUIRE_ATTESTATION
      enforcementMode: ENFORCED_BLOCK_AND_AUDIT_LOG
    clusterAdmissionRules:
      us-central1-c.prod-cluster:
        requireAttestationsBy:
        - projects/PROJECT_ID/attestors/prod-attestor
        evaluationMode: REQUIRE_ATTESTATION
        enforcementMode: ENFORCED_BLOCK_AND_AUDIT_LOG
EOF
```

### 問題25 (4点)
SBOMを生成し、依存関係の脆弱性を確認してください。

**解答例:**
```bash
# syftを使用してSBOM生成
curl -sSfL https://raw.githubusercontent.com/anchore/syft/main/install.sh | sh -s -- -b /usr/local/bin

# SBOM生成
syft packages nginx:latest -o spdx-json > nginx-sbom.spdx.json

# 脆弱性確認
grype nginx:latest
```

---

## 🔍 Domain 6: Monitoring, Logging and Runtime Security (20問)

### 問題26 (4点)
Falcoをインストールし、カスタムルールを作成して不審なプロセス実行を検出してください。

**解答例:**
```bash
# Falcoインストール
curl -s https://falco.org/repo/falcosecurity-3672BA8F.asc | apt-key add -
echo "deb https://download.falco.org/packages/deb stable main" | tee -a /etc/apt/sources.list.d/falcosecurity.list
apt-get update -y
apt-get install -y falco

# カスタムルール作成
cat >> /etc/falco/falco_rules.local.yaml << EOF
- rule: Suspicious Shell Activity
  desc: Detect shell activity in containers
  condition: >
    spawned_process and
    container and
    proc.name in (sh, bash, zsh) and
    not proc.pname in (kubelet, dockerd)
  output: >
    Shell spawned in container (user=%user.name container_id=%container.id 
    container_name=%container.name shell=%proc.name parent=%proc.pname)
  priority: WARNING
  tags: [shell, container]
EOF

# Falco起動
systemctl enable falco
systemctl start falco
```

### 問題27 (4点)
Audit loggingを設定し、セキュリティ関連のAPI呼び出しを記録してください。

**解答例:**
```bash
# Audit Policy作成
cat > /etc/kubernetes/audit-policy.yaml << EOF
apiVersion: audit.k8s.io/v1
kind: Policy
rules:
- level: RequestResponse
  resources:
  - group: ""
    resources: ["secrets", "configmaps"]
- level: Request
  resources:
  - group: ""
    resources: ["pods", "services"]
  verbs: ["create", "update", "delete"]
- level: Metadata
  resources:
  - group: "rbac.authorization.k8s.io"
    resources: ["roles", "rolebindings", "clusterroles", "clusterrolebindings"]
EOF

# API Server設定更新
vim /etc/kubernetes/manifests/kube-apiserver.yaml
# 以下を追加：
# --audit-log-path=/var/log/audit.log
# --audit-policy-file=/etc/kubernetes/audit-policy.yaml
```

### 問題28 (4点)
Runtime security monitoring のため、不正なファイルアクセスを検出するルールを作成してください。

**解答例:**
```bash
cat >> /etc/falco/falco_rules.local.yaml << EOF
- rule: Sensitive File Access
  desc: Detect access to sensitive files
  condition: >
    open_read and
    container and
    fd.name in (/etc/passwd, /etc/shadow, /etc/ssh/sshd_config, /root/.ssh/authorized_keys)
  output: >
    Sensitive file accessed (user=%user.name container_id=%container.id 
    file=%fd.name proc=%proc.name cmdline=%proc.cmdline)
  priority: HIGH
  tags: [filesystem, sensitive]
EOF
```

### 問題29 (4点)
コンテナのネットワーク通信を監視し、異常な通信を検出してください。

**解答例:**
```bash
cat >> /etc/falco/falco_rules.local.yaml << EOF
- rule: Unexpected Outbound Connection
  desc: Detect unexpected outbound connections
  condition: >
    outbound and
    container and
    not proc.name in (curl, wget, apt, yum) and
    fd.sip.name != "127.0.0.1" and
    not fd.sport in (80, 443, 53)
  output: >
    Unexpected outbound connection (container=%container.name dest=%fd.rip:%fd.rport 
    proc=%proc.name cmdline=%proc.cmdline)
  priority: WARNING
  tags: [network, outbound]
EOF
```

### 問題30 (4点)
Intrusion detection のため、権限昇格の試行を検出するルールを作成してください。

**解答例:**
```bash
cat >> /etc/falco/falco_rules.local.yaml << EOF
- rule: Privilege Escalation Attempt
  desc: Detect privilege escalation attempts
  condition: >
    spawned_process and
    container and
    proc.name in (sudo, su, passwd, chsh, chfn, chage) and
    not user.name in (root)
  output: >
    Privilege escalation attempt (user=%user.name container_id=%container.id 
    proc=%proc.name cmdline=%proc.cmdline)
  priority: CRITICAL
  tags: [privilege_escalation]
EOF
```

---

## 📊 採点基準

### Domain別配点
- **Cluster Setup (10%)**: 10点
- **Cluster Hardening (15%)**: 15点
- **System Hardening (15%)**: 15点
- **Minimize Microservice Vulnerabilities (20%)**: 20点
- **Supply Chain Security (20%)**: 20点
- **Monitoring, Logging and Runtime Security (20%)**: 20点

### 総合評価
- **90-100点**: Excellent - 実務で十分に活用できるレベル
- **80-89点**: Good - 基本的なセキュリティ実装が可能
- **67-79点**: Pass - 試験合格レベル
- **66点以下**: Fail - 追加学習が必要

## 🎯 試験のポイント

### 時間配分の目安
- Domain 1 (10問): 12分
- Domain 2 (15問): 18分
- Domain 3 (15問): 18分
- Domain 4 (20問): 24分
- Domain 5 (20問): 24分
- Domain 6 (20問): 24分

### 重要なコマンド
```bash
# エイリアス設定
alias k=kubectl
export do='--dry-run=client -o yaml'

# セキュリティ確認
k auth can-i --list --as=system:serviceaccount:default:sa
k get networkpolicy -A
k get podsecuritypolicy
```

### よくある間違い
1. YAML インデントエラー
2. 名前空間の指定忘れ
3. セキュリティコンテキストの設定ミス
4. RBAC権限の過剰付与
5. Network Policyの論理エラー

---

**重要**: この練習問題を制限時間内で解けるようになることが、CKS試験合格の重要な指標です。実際の試験環境に近い条件で練習することをお勧めします。