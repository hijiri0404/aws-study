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

### 問題37 (4点)
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

### 問題38 (4点)
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

### 問題39 (4点)
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

### 問題40 (4点)
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

### 問題41 (3点)
コンテナイメージのベースイメージを最小化し、distrolessイメージを使用してください。

**解答例:**
```bash
cat << EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: distroless-app
spec:
  containers:
  - name: app
    image: gcr.io/distroless/java:11
    command: ["java", "-jar", "app.jar"]
    securityContext:
      allowPrivilegeEscalation: false
      readOnlyRootFilesystem: true
      runAsNonRoot: true
      capabilities:
        drop:
        - ALL
EOF
```

### 問題42 (3点)
Falcoを使用して実行時の異常検知ルールを設定してください。

**解答例:**
```bash
# Falcoルール設定
cat << EOF > /etc/falco/falco_rules.local.yaml
- rule: Suspicious Container Activity
  desc: Detect suspicious activity in containers
  condition: spawned_process and container and proc.name in (nc, ncat, netcat)
  output: Suspicious network tool executed (user=%user.name command=%proc.cmdline container=%container.name)
  priority: WARNING
EOF

# Falco再起動
sudo systemctl restart falco
```

### 問題43 (3点)
NetworkPolicyを使用してマイクロサービス間の通信を制限してください。

**解答例:**
```bash
cat << EOF | kubectl apply -f -
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: frontend-netpol
  namespace: production
spec:
  podSelector:
    matchLabels:
      app: frontend
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: ingress-nginx
    ports:
    - protocol: TCP
      port: 80
  egress:
  - to:
    - podSelector:
        matchLabels:
          app: backend
    ports:
    - protocol: TCP
      port: 8080
  - to: []
    ports:
    - protocol: UDP
      port: 53
EOF
```

### 問題44 (3点)
Resource Quotaを設定し、マイクロサービスのリソース使用量を制限してください。

**解答例:**
```bash
cat << EOF | kubectl apply -f -
apiVersion: v1
kind: ResourceQuota
metadata:
  name: microservice-quota
  namespace: production
spec:
  hard:
    requests.cpu: "4"
    requests.memory: 8Gi
    limits.cpu: "8"
    limits.memory: 16Gi
    pods: "10"
    secrets: "5"
    configmaps: "5"
EOF
```

### 問題45 (3点)
LimitRangeを使用してコンテナの最小・最大リソースを制御してください。

**解答例:**
```bash
cat << EOF | kubectl apply -f -
apiVersion: v1
kind: LimitRange
metadata:
  name: microservice-limits
  namespace: production
spec:
  limits:
  - type: Container
    default:
      cpu: 100m
      memory: 128Mi
    defaultRequest:
      cpu: 50m
      memory: 64Mi
    min:
      cpu: 10m
      memory: 32Mi
    max:
      cpu: 500m
      memory: 512Mi
EOF
```

### 問題46 (2点)
コンテナ内での特権エスカレーションを防止する設定を実装してください。

**解答例:**
```bash
cat << EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: no-privilege-escalation
spec:
  containers:
  - name: app
    image: nginx:alpine
    securityContext:
      allowPrivilegeEscalation: false
      runAsNonRoot: true
      runAsUser: 1001
      capabilities:
        drop:
        - ALL
EOF
```

### 問題47 (2点)
PodDisruptionBudgetを設定し、マイクロサービスの可用性を保護してください。

**解答例:**
```bash
cat << EOF | kubectl apply -f -
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: frontend-pdb
  namespace: production
spec:
  minAvailable: 2
  selector:
    matchLabels:
      app: frontend
EOF
```

### 問題48 (2点)
サービスアカウントトークンの自動マウントを無効化してください。

**解答例:**
```bash
cat << EOF | kubectl apply -f -
apiVersion: v1
kind: ServiceAccount
metadata:
  name: secure-sa
  namespace: production
automountServiceAccountToken: false
---
apiVersion: v1
kind: Pod
metadata:
  name: secure-pod
spec:
  serviceAccountName: secure-sa
  automountServiceAccountToken: false
  containers:
  - name: app
    image: nginx:alpine
EOF
```

### 問題49 (2点)
initContainerを使用してアプリケーションコンテナの初期化を安全に実行してください。

**解答例:**
```bash
cat << EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: secure-init-pod
spec:
  initContainers:
  - name: init-security
    image: busybox:1.35
    command: ['sh', '-c', 'echo "Security checks completed"']
    securityContext:
      allowPrivilegeEscalation: false
      readOnlyRootFilesystem: true
      runAsNonRoot: true
      runAsUser: 1000
      capabilities:
        drop:
        - ALL
  containers:
  - name: app
    image: nginx:alpine
    securityContext:
      allowPrivilegeEscalation: false
      readOnlyRootFilesystem: true
      runAsNonRoot: true
      runAsUser: 101
      capabilities:
        drop:
        - ALL
EOF
```

### 問題50 (2点)
HorizontalPodAutoscalerを設定し、負荷に応じたスケーリングを実装してください。

**解答例:**
```bash
cat << EOF | kubectl apply -f -
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: frontend-hpa
  namespace: production
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: frontend
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
EOF
```

### 問題51 (2点)
セキュアな環境変数管理のため、Secretを使用してください。

**解答例:**
```bash
# Secret作成
kubectl create secret generic app-secrets \
  --from-literal=database-url="postgres://user:pass@db:5432/app" \
  --from-literal=api-key="secret-api-key-123"

# Pod でSecret使用
cat << EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: secure-env-pod
spec:
  containers:
  - name: app
    image: nginx:alpine
    env:
    - name: DATABASE_URL
      valueFrom:
        secretKeyRef:
          name: app-secrets
          key: database-url
    - name: API_KEY
      valueFrom:
        secretKeyRef:
          name: app-secrets
          key: api-key
EOF
```

### 問題52 (2点)
VerticalPodAutoscalerを設定し、リソース推奨値に基づく最適化を実装してください。

**解答例:**
```bash
cat << EOF | kubectl apply -f -
apiVersion: autoscaling.k8s.io/v1
kind: VerticalPodAutoscaler
metadata:
  name: frontend-vpa
  namespace: production
spec:
  targetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: frontend
  updatePolicy:
    updateMode: "Auto"
  resourcePolicy:
    containerPolicies:
    - containerName: frontend
      maxAllowed:
        cpu: 500m
        memory: 512Mi
      minAllowed:
        cpu: 50m
        memory: 64Mi
EOF
```

### 問題53 (1点)
Pod間のネットワーク暗号化を有効化してください。

**解答例:**
```bash
# Calico でWireGuard暗号化有効化
calicoctl patch felixconfiguration default --patch='{"spec":{"wireguardEnabled":true}}'

# または kubectl 使用
kubectl patch felixconfiguration default --type merge --patch='{"spec":{"wireguardEnabled":true}}'
```

### 問題54 (1点)
NamespaceにDefaultNetworkPolicyを適用し、デフォルト拒否を設定してください。

**解答例:**
```bash
cat << EOF | kubectl apply -f -
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-all
  namespace: production
spec:
  podSelector: {}
  policyTypes:
  - Ingress
  - Egress
EOF
```

### 問題55 (1点)
コンテナの実行時間制限を設定してください。

**解答例:**
```bash
cat << EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: time-limited-pod
spec:
  activeDeadlineSeconds: 600  # 10分で強制終了
  containers:
  - name: app
    image: busybox
    command: ["sleep", "3600"]
    securityContext:
      allowPrivilegeEscalation: false
      runAsNonRoot: true
      runAsUser: 1000
EOF
```

---

## 🔐 Domain 5: Supply Chain Security (20問)

### 問題56 (4点)
Trivyを使用してコンテナイメージの脆弱性スキャンを実行し、HIGH以上の脆弱性がないことを確認してください。

**解答例:**
```bash
# Trivyインストール
curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh | sh -s -- -b /usr/local/bin

# イメージスキャン
trivy image --severity HIGH,CRITICAL nginx:latest
trivy image --severity HIGH,CRITICAL --exit-code 1 nginx:latest
```

### 問題57 (4点)
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

### 問題58 (4点)
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

### 問題59 (4点)
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

### 問題60 (4点)
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

### 問題61 (3点)
イメージのベースOSを最小化し、alpine linuxベースのイメージを使用してください。

**解答例:**
```bash
cat << EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: alpine-app
spec:
  containers:
  - name: app
    image: nginx:alpine
    securityContext:
      allowPrivilegeEscalation: false
      readOnlyRootFilesystem: true
      runAsNonRoot: true
      runAsUser: 101
      capabilities:
        drop:
        - ALL
EOF
```

### 問題62 (3点)
コンテナイメージスキャンをCI/CDパイプラインに統合してください。

**解答例:**
```bash
# GitHub Actions でのスキャン例
cat << EOF > .github/workflows/security-scan.yml
name: Security Scan
on: [push, pull_request]
jobs:
  scan:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - name: Build image
      run: docker build -t myapp:latest .
    - name: Run Trivy scanner
      uses: aquasecurity/trivy-action@master
      with:
        image-ref: 'myapp:latest'
        format: 'sarif'
        output: 'trivy-results.sarif'
        severity: 'CRITICAL,HIGH'
        exit-code: '1'
EOF
```

### 問題63 (3点)
OPA Conftest を使用してKubernetes YAMLファイルのポリシー検証を実装してください。

**解答例:**
```bash
# Conftest インストール
curl -L https://github.com/open-policy-agent/conftest/releases/latest/download/conftest_Linux_x86_64.tar.gz | tar xz
sudo mv conftest /usr/local/bin

# ポリシー作成
cat << EOF > policy.rego
package main

deny[msg] {
  input.kind == "Pod"
  input.spec.securityContext.runAsRoot == true
  msg := "Pod must not run as root"
}

deny[msg] {
  input.kind == "Pod"
  not input.spec.securityContext.readOnlyRootFilesystem
  msg := "Pod must have read-only root filesystem"
}
EOF

# ポリシー検証実行
conftest test --policy policy.rego pod.yaml
```

### 問題64 (3点)
AdmissionReviewを使用してカスタムAdmission Controllerを作成してください。

**解答例:**
```bash
cat << EOF | kubectl apply -f -
apiVersion: admissionregistration.k8s.io/v1
kind: ValidatingAdmissionWebhook
metadata:
  name: security-validator
webhooks:
- name: security.example.com
  clientConfig:
    service:
      name: security-webhook
      namespace: security
      path: "/validate"
  rules:
  - operations: ["CREATE", "UPDATE"]
    apiGroups: [""]
    apiVersions: ["v1"]
    resources: ["pods"]
  admissionReviewVersions: ["v1"]
  sideEffects: None
  failurePolicy: Fail
EOF
```

### 問題65 (3点)
イメージスキャン結果をPrometheusメトリクスとして出力してください。

**解答例:**
```bash
# カスタムメトリクス出力スクリプト
cat << EOF > scan-metrics.sh
#!/bin/bash
RESULT=\$(trivy image --format json nginx:latest)
HIGH_COUNT=\$(echo \$RESULT | jq '[.Results[]?.Vulnerabilities[]? | select(.Severity == "HIGH")] | length')
CRITICAL_COUNT=\$(echo \$RESULT | jq '[.Results[]?.Vulnerabilities[]? | select(.Severity == "CRITICAL")] | length')

cat << METRICS > /tmp/image-scan-metrics.txt
# HELP image_vulnerabilities_total Total number of vulnerabilities found
# TYPE image_vulnerabilities_total gauge
image_vulnerabilities_total{severity="high",image="nginx:latest"} \$HIGH_COUNT
image_vulnerabilities_total{severity="critical",image="nginx:latest"} \$CRITICAL_COUNT
METRICS
EOF

chmod +x scan-metrics.sh
```

### 問題66 (3点)
コンテナランタイムに Gvisor を設定し、サンドボックス環境を構築してください。

**解答例:**
```bash
# gVisor インストール
curl -fsSL https://gvisor.dev/archive.key | sudo gpg --dearmor -o /usr/share/keyrings/gvisor-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/gvisor-archive-keyring.gpg] https://storage.googleapis.com/gvisor/releases release main" | sudo tee /etc/apt/sources.list.d/gvisor.list > /dev/null
sudo apt-get update && sudo apt-get install -y runsc

# RuntimeClass 作成
cat << EOF | kubectl apply -f -
apiVersion: node.k8s.io/v1
kind: RuntimeClass
metadata:
  name: gvisor
handler: runsc
EOF
```

### 問題67 (2点)
イメージに含まれる機密情報をスキャンしてください。

**解答例:**
```bash
# truffleHog を使用
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
  trufflesecurity/trufflehog:latest docker --image nginx:latest

# または GitLeaks
docker run --rm -v \$(pwd):/scan zricethezav/gitleaks:latest detect --source /scan
```

### 問題68 (2点)
コンテナイメージの脆弱性データベースを定期更新してください。

**解答例:**
```bash
# Trivy DB 更新スクリプト
cat << EOF > update-trivy-db.sh
#!/bin/bash
echo "Updating Trivy vulnerability database..."
trivy --download-db-only
echo "Database update completed at \$(date)"
EOF

# Crontab に追加
(crontab -l 2>/dev/null; echo "0 6 * * * /path/to/update-trivy-db.sh") | crontab -
```

### 問題69 (2点)
ネットワークポリシーでイメージレジストリへのアクセスを制限してください。

**解答例:**
```bash
cat << EOF | kubectl apply -f -
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: registry-access-policy
  namespace: production
spec:
  podSelector: {}
  policyTypes:
  - Egress
  egress:
  - to:
    - namespaceSelector:
        matchLabels:
          name: kube-system
    ports:
    - protocol: UDP
      port: 53
  - to: []
    ports:
    - protocol: TCP
      port: 443
    - protocol: TCP
      port: 80
    # 承認されたレジストリのみ
    namespaceSelector:
      matchLabels:
        registry: "approved"
EOF
```

### 問題70 (2点)
プライベートレジストリへの認証情報を安全に管理してください。

**解答例:**
```bash
# Docker registry secret 作成
kubectl create secret docker-registry registry-secret \
  --docker-server=registry.company.com \
  --docker-username=user \
  --docker-password=password \
  --docker-email=user@company.com

# Pod でSecret使用
cat << EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: private-registry-pod
spec:
  imagePullSecrets:
  - name: registry-secret
  containers:
  - name: app
    image: registry.company.com/private-app:latest
EOF
```

### 問題71 (2点)
イメージのライセンス情報を確認してください。

**解答例:**
```bash
# syft でライセンス情報取得
syft packages nginx:latest -o json | jq '.artifacts[] | select(.licenses != null) | {name: .name, licenses: .licenses}'

# または Tern を使用
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
  ternd/tern:latest report -i nginx:latest
```

### 問題72 (2点)
マルチステージビルドを使用してイメージサイズを最小化してください。

**解答例:**
```dockerfile
# Dockerfile例
FROM golang:1.19-alpine AS builder
WORKDIR /app
COPY . .
RUN go build -o main .

FROM gcr.io/distroless/static:nonroot
WORKDIR /
COPY --from=builder /app/main .
USER 65532:65532
ENTRYPOINT ["./main"]
```

### 問題73 (1点)
.dockerignore を設定して不要なファイルのイメージ組み込みを防止してください。

**解答例:**
```bash
cat << EOF > .dockerignore
.git
.gitignore
README.md
Dockerfile
.dockerignore
node_modules
npm-debug.log
.env
*.md
.DS_Store
EOF
```

### 問題74 (1点)
イメージスキャン結果を JSON 形式で出力し、フィルタリングしてください。

**解答例:**
```bash
# 高危険度の脆弱性のみ表示
trivy image --format json nginx:latest | jq '.Results[] | .Vulnerabilities[] | select(.Severity == "HIGH" or .Severity == "CRITICAL") | {ID: .VulnerabilityID, Severity: .Severity, Package: .PkgName}'
```

### 問題75 (1点)
コンテナイメージの作成者情報を確認してください。

**解答例:**
```bash
# イメージメタデータ確認
docker inspect nginx:latest | jq '.[0].Config.Labels'

# または Cosign での attestation 確認
cosign verify-attestation --key cosign.pub nginx:latest
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

### 問題76 (4点)
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

### 問題77 (4点)
Fluent Bitを使用してKubernetesのログを集約し、セキュリティイベントをフィルタリングしてください。

**解答例:**
```bash
# Fluent Bit設定
cat << EOF | kubectl apply -f -
apiVersion: v1
kind: ConfigMap
metadata:
  name: fluent-bit-config
  namespace: kube-system
data:
  fluent-bit.conf: |
    [SERVICE]
        Flush         1
        Log_Level     info
        Daemon        off
        Parsers_File  parsers.conf
    
    [INPUT]
        Name              tail
        Path              /var/log/audit/audit.log
        Parser            audit
        Tag               audit.*
        Refresh_Interval  5
    
    [FILTER]
        Name    grep
        Match   audit.*
        Regex   verb (create|update|delete)
    
    [OUTPUT]
        Name  es
        Match audit.*
        Host  elasticsearch.logging.svc.cluster.local
        Port  9200
        Index security-audit
  
  parsers.conf: |
    [PARSER]
        Name   audit
        Format json
        Time_Key timestamp
        Time_Format %Y-%m-%dT%H:%M:%S.%LZ
EOF

# DaemonSet作成
cat << EOF | kubectl apply -f -
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: fluent-bit
  namespace: kube-system
spec:
  selector:
    matchLabels:
      name: fluent-bit
  template:
    metadata:
      labels:
        name: fluent-bit
    spec:
      serviceAccountName: fluent-bit
      containers:
      - name: fluent-bit
        image: fluent/fluent-bit:2.0
        volumeMounts:
        - name: config
          mountPath: /fluent-bit/etc/
        - name: varlog
          mountPath: /var/log
        - name: varlibdockercontainers
          mountPath: /var/lib/docker/containers
      volumes:
      - name: config
        configMap:
          name: fluent-bit-config
      - name: varlog
        hostPath:
          path: /var/log
      - name: varlibdockercontainers
        hostPath:
          path: /var/lib/docker/containers
EOF
```

### 問題78 (4点)
Prometheusアラートルールを作成して、セキュリティメトリクスの異常を検知してください。

**解答例:**
```bash
cat << EOF | kubectl apply -f -
apiVersion: v1
kind: ConfigMap
metadata:
  name: security-alerts
  namespace: monitoring
data:
  security-rules.yaml: |
    groups:
    - name: security.rules
      rules:
      - alert: HighFailedLogins
        expr: rate(login_failures_total[5m]) > 10
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "High failed login rate detected"
          description: "{{ $value }} failed logins per second"
      
      - alert: SuspiciousAPICall
        expr: rate(apiserver_audit_requests_total{verb="delete",objectRef_resource="secrets"}[5m]) > 1
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Suspicious secret deletion detected"
          description: "Secrets being deleted at {{ $value }} per second"
      
      - alert: ContainerRootExecution
        expr: container_processes{user="root"} > 0
        for: 0m
        labels:
          severity: high
        annotations:
          summary: "Container running as root user"
          description: "Pod {{ $labels.pod }} running as root"
EOF
```

### 问题79 (4点)
OpenTelemetryコレクターを設定して分散トレーシングでセキュリティイベントを追跡してください。

**解答例:**
```bash
# OpenTelemetry Collector設定
cat << EOF | kubectl apply -f -
apiVersion: v1
kind: ConfigMap
metadata:
  name: otel-collector-config
  namespace: security
data:
  config.yaml: |
    receivers:
      jaeger:
        protocols:
          grpc:
            endpoint: 0.0.0.0:14250
          thrift_http:
            endpoint: 0.0.0.0:14268
      zipkin:
        endpoint: 0.0.0.0:9411
    
    processors:
      attributes:
        actions:
          - key: security.event
            action: insert
            value: "authentication"
      filter:
        spans:
          include:
            attributes:
              - key: "security.level"
                value: "high"
    
    exporters:
      jaeger:
        endpoint: jaeger-collector.security.svc.cluster.local:14250
        tls:
          insecure: true
      logging:
        loglevel: debug
    
    service:
      pipelines:
        traces:
          receivers: [jaeger, zipkin]
          processors: [attributes, filter]
          exporters: [jaeger, logging]
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: otel-collector
  namespace: security
spec:
  replicas: 1
  selector:
    matchLabels:
      app: otel-collector
  template:
    metadata:
      labels:
        app: otel-collector
    spec:
      containers:
      - name: otel-collector
        image: otel/opentelemetry-collector:latest
        args: ["--config=/etc/otel-collector-config/config.yaml"]
        volumeMounts:
        - name: config
          mountPath: /etc/otel-collector-config
      volumes:
      - name: config
        configMap:
          name: otel-collector-config
EOF
```

### 問題80 (3点)
Grafanaダッシュボードを作成してセキュリティメトリクスを可視化してください。

**解答例:**
```bash
cat << EOF | kubectl apply -f -
apiVersion: v1
kind: ConfigMap
metadata:
  name: security-dashboard
  namespace: monitoring
data:
  security-dashboard.json: |
    {
      "dashboard": {
        "title": "Kubernetes Security Dashboard",
        "panels": [
          {
            "title": "Failed Authentication Attempts",
            "type": "graph",
            "targets": [
              {
                "expr": "rate(authentication_attempts_total{result=\"failure\"}[5m])",
                "legendFormat": "{{method}} failures"
              }
            ]
          },
          {
            "title": "Pod Security Policy Violations",
            "type": "stat",
            "targets": [
              {
                "expr": "increase(psp_violations_total[1h])",
                "legendFormat": "PSP Violations"
              }
            ]
          },
          {
            "title": "Network Policy Denials",
            "type": "heatmap",
            "targets": [
              {
                "expr": "rate(network_policy_denials_total[5m])",
                "legendFormat": "{{namespace}}"
              }
            ]
          }
        ]
      }
    }
EOF
```

### 問題81 (3点)
ElasticsearchとKibanaを使用してセキュリティログの検索・分析環境を構築してください。

**解答例:**
```bash
# Elasticsearch設定
cat << EOF | kubectl apply -f -
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: elasticsearch
  namespace: logging
spec:
  serviceName: elasticsearch
  replicas: 1
  selector:
    matchLabels:
      app: elasticsearch
  template:
    metadata:
      labels:
        app: elasticsearch
    spec:
      containers:
      - name: elasticsearch
        image: docker.elastic.co/elasticsearch/elasticsearch:7.17.0
        ports:
        - containerPort: 9200
        - containerPort: 9300
        env:
        - name: discovery.type
          value: single-node
        - name: ES_JAVA_OPTS
          value: "-Xms512m -Xmx512m"
        - name: xpack.security.enabled
          value: "true"
        - name: ELASTIC_PASSWORD
          value: "changeme"
        volumeMounts:
        - name: data
          mountPath: /usr/share/elasticsearch/data
  volumeClaimTemplates:
  - metadata:
      name: data
    spec:
      accessModes: ["ReadWriteOnce"]
      resources:
        requests:
          storage: 10Gi
---
apiVersion: v1
kind: Service
metadata:
  name: elasticsearch
  namespace: logging
spec:
  selector:
    app: elasticsearch
  ports:
  - port: 9200
    targetPort: 9200
EOF

# Kibana設定
cat << EOF | kubectl apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: kibana
  namespace: logging
spec:
  replicas: 1
  selector:
    matchLabels:
      app: kibana
  template:
    metadata:
      labels:
        app: kibana
    spec:
      containers:
      - name: kibana
        image: docker.elastic.co/kibana/kibana:7.17.0
        ports:
        - containerPort: 5601
        env:
        - name: ELASTICSEARCH_HOSTS
          value: "http://elasticsearch:9200"
        - name: ELASTICSEARCH_USERNAME
          value: "elastic"
        - name: ELASTICSEARCH_PASSWORD
          value: "changeme"
EOF
```

### 问题82 (3点)
SIEMツール（Security Information and Event Management）のルールを作成してください。

**解答例:**
```bash
# Elasticsearchクエリルール
cat << EOF > siem-rules.json
{
  "rules": [
    {
      "name": "Multiple Failed Logins",
      "query": {
        "bool": {
          "must": [
            {"match": {"event.action": "authentication"}},
            {"match": {"event.outcome": "failure"}},
            {"range": {"@timestamp": {"gte": "now-5m"}}}
          ]
        }
      },
      "threshold": 5,
      "actions": [
        {
          "type": "webhook",
          "url": "http://alertmanager:9093/api/v1/alerts"
        }
      ]
    },
    {
      "name": "Privilege Escalation",
      "query": {
        "bool": {
          "must": [
            {"match": {"process.name": "sudo"}},
            {"match": {"container.id": "*"}},
            {"range": {"@timestamp": {"gte": "now-1m"}}}
          ]
        }
      },
      "threshold": 1,
      "priority": "high"
    }
  ]
}
EOF

# ルール適用スクリプト
cat << EOF > apply-siem-rules.sh
#!/bin/bash
curl -X POST "elasticsearch:9200/_watcher/watch/security-alerts" \
  -H 'Content-Type: application/json' \
  -d @siem-rules.json
EOF
```

### 問題83 (3点)
不審なプロセス実行をリアルタイムで検出する監視システムを構築してください。

**解答例:**
```bash
# Falco + Sidekick設定
cat << EOF | kubectl apply -f -
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: falco-sidekick
  namespace: falco
spec:
  selector:
    matchLabels:
      app: falco-sidekick
  template:
    metadata:
      labels:
        app: falco-sidekick
    spec:
      containers:
      - name: falco-sidekick
        image: falcosecurity/falcosidekick:latest
        env:
        - name: SLACK_WEBHOOKURL
          value: "https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK"
        - name: ELASTICSEARCH_HOSTPORT
          value: "elasticsearch.logging:9200"
        - name: LOKI_HOSTPORT
          value: "http://loki.logging:3100"
        ports:
        - containerPort: 2801
---
apiVersion: v1
kind: Service
metadata:
  name: falco-sidekick
  namespace: falco
spec:
  selector:
    app: falco-sidekick
  ports:
  - port: 2801
    targetPort: 2801
EOF

# Falco設定更新
cat >> /etc/falco/falco.yaml << EOF
json_output: true
json_include_output_property: true
http_output:
  enabled: true
  url: "http://falco-sidekick.falco:2801/"
EOF
```

### 問題84 (3点)
Jaegerを使用してマイクロサービス間の通信をトレースし、セキュリティ異常を検出してください。

**解答例:**
```bash
# Jaeger Operator設定
cat << EOF | kubectl apply -f -
apiVersion: jaegertracing.io/v1
kind: Jaeger
metadata:
  name: security-jaeger
  namespace: observability
spec:
  strategy: production
  storage:
    type: elasticsearch
    elasticsearch:
      nodeCount: 1
      resources:
        requests:
          memory: "2Gi"
          cpu: "500m"
        limits:
          memory: "2Gi"
  collector:
    resources:
      requests:
        memory: "100Mi"
        cpu: "100m"
  query:
    resources:
      requests:
        memory: "100Mi"
        cpu: "100m"
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: jaeger-security-config
  namespace: observability
data:
  config.yaml: |
    processors:
      - name: security-attributes
        config:
          rules:
            - name: detect-suspicious-calls
              condition: 'span.tags["http.status_code"] >= 400'
              action: 
                type: tag
                key: security.alert
                value: suspicious_http_error
EOF
```

### 問題85 (3点)
ログ相関分析を実装して攻撃パターンを検出してください。

**解答例:**
```bash
# Logstash設定
cat << EOF | kubectl apply -f -
apiVersion: v1
kind: ConfigMap
metadata:
  name: logstash-config
  namespace: logging
data:
  logstash.conf: |
    input {
      beats {
        port => 5044
      }
    }
    
    filter {
      if [kubernetes][container][name] == "nginx" {
        grok {
          match => { "message" => "%{COMBINEDAPACHELOG}" }
        }
        
        # 攻撃パターン検出
        if [response] >= 400 {
          mutate {
            add_tag => ["http_error"]
          }
        }
        
        # SQLインジェクション検出
        if [request] =~ /union|select|insert|delete|drop/i {
          mutate {
            add_tag => ["sql_injection_attempt"]
            add_field => { "security_alert" => "sql_injection" }
          }
        }
        
        # XSS検出
        if [request] =~ /<script|javascript:|onload=|onerror=/i {
          mutate {
            add_tag => ["xss_attempt"]
            add_field => { "security_alert" => "xss" }
          }
        }
      }
      
      # 相関分析 - 同一IPからの大量リクエスト
      aggregate {
        task_id => "%{clientip}"
        code => "
          map['request_count'] ||= 0
          map['request_count'] += 1
          if map['request_count'] > 100
            event.set('security_alert', 'rate_limit_exceeded')
            event.set('alert_level', 'high')
          end
        "
        push_map_as_event_on_timeout => true
        timeout_task_id_field => "clientip"
        timeout => 300
      }
    }
    
    output {
      if [security_alert] {
        elasticsearch {
          hosts => ["elasticsearch:9200"]
          index => "security-alerts-%{+YYYY.MM.dd}"
        }
        
        http {
          url => "http://alertmanager:9093/api/v1/alerts"
          http_method => "post"
          content_type => "application/json"
          format => "json"
        }
      }
      
      elasticsearch {
        hosts => ["elasticsearch:9200"]
        index => "kubernetes-logs-%{+YYYY.MM.dd}"
      }
    }
EOF
EOF
```

### 問題86 (2点)
セキュリティインシデント対応の自動化スクリプトを作成してください。

**解答例:**
```bash
cat << 'EOF' > incident-response.sh
#!/bin/bash

# インシデント対応自動化スクリプト
ALERT_TYPE=$1
NAMESPACE=$2
POD_NAME=$3

case $ALERT_TYPE in
  "malicious_process")
    echo "Malicious process detected in pod $POD_NAME"
    
    # Pod isolation
    kubectl label pod $POD_NAME -n $NAMESPACE security.incident=true
    kubectl annotate pod $POD_NAME -n $NAMESPACE incident.timestamp=$(date -Iseconds)
    
    # Network isolation
    cat << EOFNP | kubectl apply -f -
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: isolate-${POD_NAME}
  namespace: $NAMESPACE
spec:
  podSelector:
    matchLabels:
      security.incident: "true"
  policyTypes:
  - Ingress
  - Egress
EOFNP
    
    # Memory dump
    kubectl exec -n $NAMESPACE $POD_NAME -- cat /proc/1/maps > /tmp/${POD_NAME}-memory-map.txt
    
    # Log collection
    kubectl logs -n $NAMESPACE $POD_NAME > /tmp/${POD_NAME}-logs.txt
    ;;
    
  "privilege_escalation")
    echo "Privilege escalation detected"
    
    # Immediate pod termination
    kubectl delete pod $POD_NAME -n $NAMESPACE --grace-period=0 --force
    
    # Audit log collection
    grep -A 10 -B 10 $POD_NAME /var/log/audit/audit.log > /tmp/audit-${POD_NAME}.log
    
    # Alert team
    curl -X POST -H 'Content-Type: application/json' \
      -d '{"text":"CRITICAL: Privilege escalation in pod '$POD_NAME'"}' \
      $SLACK_WEBHOOK_URL
    ;;
esac

# Store evidence
tar -czf /tmp/incident-$(date +%Y%m%d-%H%M%S).tar.gz /tmp/${POD_NAME}*

echo "Incident response completed for $ALERT_TYPE"
EOF

chmod +x incident-response.sh
```

### 問題87 (2点)
暗号化されたログストレージを実装してください。

**解答例:**
```bash
# 暗号化キー生成
kubectl create secret generic log-encryption-key \
  --from-literal=key=$(openssl rand -base64 32) \
  -n logging

# Fluent Bit 暗号化設定
cat << EOF | kubectl apply -f -
apiVersion: v1
kind: ConfigMap
metadata:
  name: fluent-bit-encryption
  namespace: logging
data:
  fluent-bit.conf: |
    [SERVICE]
        Flush         1
        Log_Level     info
        Parsers_File  parsers.conf
    
    [INPUT]
        Name              tail
        Path              /var/log/containers/*.log
        Parser            cri
        Tag               kube.*
        Refresh_Interval  5
    
    [FILTER]
        Name    lua
        Match   kube.*
        Script  encrypt.lua
        Call    encrypt_log
    
    [OUTPUT]
        Name  s3
        Match kube.*
        bucket security-logs-encrypted
        region us-west-2
        use_put_object On
        compression gzip
  
  encrypt.lua: |
    function encrypt_log(tag, timestamp, record)
        local json = require "json"
        local log_string = json.encode(record)
        
        -- 実際の暗号化処理（簡略化）
        record["encrypted_payload"] = log_string
        record["encryption_version"] = "v1"
        
        return 1, timestamp, record
    end
  
  parsers.conf: |
    [PARSER]
        Name        cri
        Format      regex
        Regex       ^(?<time>[^ ]+) (?<stream>stdout|stderr) (?<logtag>[^ ]*) (?<message>.*)$
        Time_Key    time
        Time_Format %Y-%m-%dT%H:%M:%S.%L%z
EOF
```

### 問題88 (2点)
コンプライアンス監査のためのログ保持ポリシーを実装してください。

**解答例:**
```bash
# ILM (Index Lifecycle Management) ポリシー
cat << EOF > audit-log-policy.json
{
  "policy": {
    "phases": {
      "hot": {
        "actions": {
          "rollover": {
            "max_size": "10gb",
            "max_age": "7d"
          }
        }
      },
      "warm": {
        "min_age": "7d",
        "actions": {
          "shrink": {
            "number_of_shards": 1
          },
          "allocate": {
            "number_of_replicas": 0
          }
        }
      },
      "cold": {
        "min_age": "30d",
        "actions": {
          "allocate": {
            "number_of_replicas": 0
          }
        }
      },
      "delete": {
        "min_age": "2555d"
      }
    }
  }
}
EOF

# ポリシー適用
curl -X PUT "elasticsearch:9200/_ilm/policy/audit-log-policy" \
  -H 'Content-Type: application/json' \
  -d @audit-log-policy.json

# インデックステンプレート作成
curl -X PUT "elasticsearch:9200/_index_template/audit-logs" \
  -H 'Content-Type: application/json' \
  -d '{
    "index_patterns": ["audit-logs-*"],
    "template": {
      "settings": {
        "index.lifecycle.name": "audit-log-policy",
        "index.lifecycle.rollover_alias": "audit-logs"
      }
    }
  }'
```

### 問題89 (2点)
異常検知のための機械学習モデルを実装してください。

**解答例:**
```bash
# Elasticsearch Machine Learning設定
cat << EOF > ml-anomaly-detection.json
{
  "job_id": "security-anomaly-detection",
  "description": "Detect anomalies in security events",
  "analysis_config": {
    "bucket_span": "15m",
    "detectors": [
      {
        "function": "high_count",
        "field_name": "user.name",
        "detector_description": "High user activity"
      },
      {
        "function": "rare",
        "field_name": "process.name",
        "detector_description": "Rare process execution"
      },
      {
        "function": "high_mean",
        "field_name": "network.bytes",
        "by_field_name": "source.ip",
        "detector_description": "High network traffic by IP"
      }
    ]
  },
  "data_description": {
    "time_field": "@timestamp",
    "time_format": "epoch_ms"
  },
  "model_snapshot_retention_days": 7,
  "results_index_name": "security-ml-anomalies"
}
EOF

# ML Job作成
curl -X PUT "elasticsearch:9200/_ml/anomaly_detectors/security-anomaly-detection" \
  -H 'Content-Type: application/json' \
  -d @ml-anomaly-detection.json

# Datafeed設定
cat << EOF > ml-datafeed.json
{
  "datafeed_id": "security-events-feed",
  "job_id": "security-anomaly-detection",
  "indices": ["security-events-*"],
  "query": {
    "bool": {
      "must": [
        {
          "range": {
            "@timestamp": {
              "gte": "now-1h"
            }
          }
        }
      ]
    }
  }
}
EOF

curl -X PUT "elasticsearch:9200/_ml/datafeeds/security-events-feed" \
  -H 'Content-Type: application/json' \
  -d @ml-datafeed.json
```

### 問題90 (2点)
リアルタイムセキュリティダッシュボードを作成してください。

**解答例:**
```bash
# Grafana Dashboard設定
cat << EOF > realtime-security-dashboard.json
{
  "dashboard": {
    "title": "Real-time Security Dashboard",
    "refresh": "5s",
    "time": {
      "from": "now-15m",
      "to": "now"
    },
    "panels": [
      {
        "title": "Active Security Threats",
        "type": "stat",
        "targets": [
          {
            "expr": "sum(rate(security_events_total{severity=\"critical\"}[1m]))",
            "legendFormat": "Critical Threats"
          }
        ],
        "fieldConfig": {
          "overrides": [
            {
              "matcher": {
                "id": "byName",
                "options": "Critical Threats"
              },
              "properties": [
                {
                  "id": "color",
                  "value": {
                    "mode": "thresholds"
                  }
                },
                {
                  "id": "thresholds",
                  "value": {
                    "steps": [
                      {"color": "green", "value": null},
                      {"color": "yellow", "value": 1},
                      {"color": "red", "value": 5}
                    ]
                  }
                }
              ]
            }
          ]
        }
      },
      {
        "title": "Failed Authentication Attempts",
        "type": "timeseries",
        "targets": [
          {
            "expr": "rate(authentication_failures_total[1m])",
            "legendFormat": "{{method}} - {{namespace}}"
          }
        ]
      },
      {
        "title": "Network Policy Violations",
        "type": "bargauge",
        "targets": [
          {
            "expr": "topk(10, sum by (namespace) (rate(network_policy_violations_total[5m])))",
            "legendFormat": "{{namespace}}"
          }
        ]
      },
      {
        "title": "Pod Security Policy Violations",
        "type": "table",
        "targets": [
          {
            "expr": "sum by (pod, namespace, violation_type) (increase(psp_violations_total[1h]))",
            "format": "table"
          }
        ]
      }
    ]
  }
}
EOF

# Dashboard import
curl -X POST "http://grafana:3000/api/dashboards/db" \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer YOUR_API_KEY' \
  -d @realtime-security-dashboard.json
```

### 問題91 (2点)
セキュリティメトリクスの自動アラート設定を実装してください。

**解答例:**
```bash
# AlertManager設定
cat << EOF | kubectl apply -f -
apiVersion: v1
kind: ConfigMap
metadata:
  name: alertmanager-config
  namespace: monitoring
data:
  alertmanager.yml: |
    global:
      slack_api_url: 'YOUR_SLACK_WEBHOOK_URL'
    
    route:
      group_by: ['alertname', 'cluster', 'service']
      group_wait: 10s
      group_interval: 10s
      repeat_interval: 1h
      receiver: 'security-team'
      routes:
      - match:
          severity: critical
        receiver: 'security-critical'
      - match:
          alertname: PodSecurityPolicyViolation
        receiver: 'security-psp'
    
    receivers:
    - name: 'security-team'
      slack_configs:
      - channel: '#security-alerts'
        title: 'Security Alert'
        text: '{{ range .Alerts }}{{ .Annotations.summary }}{{ end }}'
    
    - name: 'security-critical'
      slack_configs:
      - channel: '#security-critical'
        title: 'CRITICAL Security Alert'
        text: '{{ range .Alerts }}{{ .Annotations.summary }}{{ end }}'
        send_resolved: true
      pagerduty_configs:
      - service_key: 'YOUR_PAGERDUTY_KEY'
    
    - name: 'security-psp'
      webhook_configs:
      - url: 'http://security-automation:8080/psp-violation'
        send_resolved: false
EOF

# Prometheus Rule
cat << EOF | kubectl apply -f -
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: security-alerts
  namespace: monitoring
spec:
  groups:
  - name: security.rules
    rules:
    - alert: CriticalSecurityViolation
      expr: increase(security_violations_total{severity="critical"}[5m]) > 0
      for: 0m
      labels:
        severity: critical
      annotations:
        summary: "Critical security violation detected"
        description: "{{ $value }} critical security violations in the last 5 minutes"
    
    - alert: SuspiciousNetworkActivity
      expr: rate(network_bytes_total[5m]) > 1000000000
      for: 2m
      labels:
        severity: warning
      annotations:
        summary: "Suspicious network activity detected"
        description: "High network traffic: {{ $value }} bytes/sec"
EOF
```

### 問題92 (1点)
ログの改ざん検知システムを実装してください。

**解答例:**
```bash
# ログハッシュ生成スクリプト
cat << 'EOF' > log-integrity-check.sh
#!/bin/bash

LOG_FILE=$1
HASH_FILE="${LOG_FILE}.sha256"

# 現在のハッシュ計算
CURRENT_HASH=$(sha256sum "$LOG_FILE" | cut -d' ' -f1)

# 前回のハッシュ確認
if [ -f "$HASH_FILE" ]; then
  PREVIOUS_HASH=$(cat "$HASH_FILE")
  if [ "$CURRENT_HASH" != "$PREVIOUS_HASH" ]; then
    echo "WARNING: Log file $LOG_FILE has been modified!"
    echo "Previous hash: $PREVIOUS_HASH"
    echo "Current hash: $CURRENT_HASH"
    
    # アラート送信
    curl -X POST -H 'Content-Type: application/json' \
      -d '{"text":"Log tampering detected in '"$LOG_FILE"'"}' \
      $SLACK_WEBHOOK_URL
  fi
fi

# 現在のハッシュ保存
echo "$CURRENT_HASH" > "$HASH_FILE"
EOF

chmod +x log-integrity-check.sh

# 定期実行設定
(crontab -l 2>/dev/null; echo "*/5 * * * * /path/to/log-integrity-check.sh /var/log/audit/audit.log") | crontab -
```

### 問題93 (1点)
セキュリティ設定の構成ドリフト検知を実装してください。

**解答例:**
```bash
# 設定ベースライン作成
cat << 'EOF' > security-baseline.sh
#!/bin/bash

# セキュリティ設定のベースライン取得
cat << BASELINE > /tmp/security-baseline.json
{
  "kubectl_config": {
    "anonymous_auth": false,
    "audit_logging": true,
    "rbac_enabled": true
  },
  "pod_security": {
    "pod_security_policy_enabled": true,
    "network_policy_enabled": true
  },
  "etcd": {
    "encryption_enabled": true,
    "tls_enabled": true
  }
}
BASELINE

# 現在の設定取得・比較
CURRENT_CONFIG=$(kubectl get configmap kube-system/cluster-info -o jsonpath='{.data.kubeconfig}')
API_SERVER_ARGS=$(ps aux | grep kube-apiserver | grep -o -- '--[^=]*=[^ ]*')

# 設定差分チェック
if ! echo "$API_SERVER_ARGS" | grep -q "anonymous-auth=false"; then
  echo "DRIFT: Anonymous auth not disabled"
fi

if ! echo "$API_SERVER_ARGS" | grep -q "audit-log-path"; then
  echo "DRIFT: Audit logging not configured"
fi

# PSP確認
if ! kubectl get psp &>/dev/null; then
  echo "DRIFT: Pod Security Policy not enabled"
fi
EOF

chmod +x security-baseline.sh
```

### 問題94 (1点)
コンテナエスケープの検知ルールを作成してください。

**解答例:**
```bash
cat >> /etc/falco/falco_rules.local.yaml << EOF
- rule: Container Escape Attempt
  desc: Detect potential container escape attempts
  condition: >
    spawned_process and
    container and
    (proc.name in (docker, runc, containerd, ctr) or
     proc.cmdline contains "mount --bind" or
     proc.cmdline contains "/proc/1/root" or
     proc.cmdline contains "nsenter" or
     proc.cmdline contains "unshare")
  output: >
    Container escape attempt detected (user=%user.name container_id=%container.id 
    proc=%proc.name cmdline=%proc.cmdline)
  priority: CRITICAL
  tags: [container_escape, privilege_escalation]

- rule: Host Mount Access
  desc: Detect access to host filesystem from container
  condition: >
    open_read and
    container and
    fd.name startswith /host and
    not proc.name in (systemd, kubelet)
  output: >
    Host filesystem access from container (user=%user.name container_id=%container.id 
    file=%fd.name proc=%proc.name)
  priority: HIGH
  tags: [container_escape, host_access]
EOF

# Falco再起動
systemctl restart falco
```

### 問題95 (1点)
セキュリティポリシーの自動更新システムを実装してください。

**解答例:**
```bash
cat << 'EOF' > policy-updater.sh
#!/bin/bash

POLICY_REPO="https://github.com/company/security-policies.git"
LOCAL_PATH="/tmp/security-policies"

# 最新ポリシー取得
git clone $POLICY_REPO $LOCAL_PATH || git -C $LOCAL_PATH pull

# NetworkPolicy更新
for policy in $LOCAL_PATH/network-policies/*.yaml; do
  kubectl apply -f "$policy"
done

# PodSecurityPolicy更新
for policy in $LOCAL_PATH/pod-security-policies/*.yaml; do
  kubectl apply -f "$policy"
done

# RBAC更新
for policy in $LOCAL_PATH/rbac/*.yaml; do
  kubectl apply -f "$policy"
done

# 適用確認
kubectl get networkpolicy -A
kubectl get psp
kubectl get clusterrole | grep security

echo "Security policies updated successfully"
EOF

chmod +x policy-updater.sh

# 定期実行設定
(crontab -l 2>/dev/null; echo "0 2 * * * /path/to/policy-updater.sh") | crontab -
```

### 問題96 (1点)
セキュリティイベントの統計レポートを自動生成してください。

**解答例:**
```bash
cat << 'EOF' > security-report.sh
#!/bin/bash

REPORT_DATE=$(date +%Y-%m-%d)
REPORT_FILE="/tmp/security-report-$REPORT_DATE.html"

cat << REPORT > $REPORT_FILE
<!DOCTYPE html>
<html>
<head>
    <title>Security Report - $REPORT_DATE</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        table { border-collapse: collapse; width: 100%; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #f2f2f2; }
        .critical { color: red; font-weight: bold; }
        .warning { color: orange; }
        .info { color: blue; }
    </style>
</head>
<body>
    <h1>Daily Security Report - $REPORT_DATE</h1>
    
    <h2>Summary</h2>
    <table>
        <tr><th>Metric</th><th>Count</th><th>Status</th></tr>
        <tr><td>Failed Logins</td><td>$(grep "authentication failure" /var/log/audit/audit.log | wc -l)</td><td class="warning">Review</td></tr>
        <tr><td>PSP Violations</td><td>$(kubectl get events -A | grep "PodSecurityPolicy" | wc -l)</td><td class="info">Normal</td></tr>
        <tr><td>Privilege Escalations</td><td>$(grep "sudo" /var/log/audit/audit.log | wc -l)</td><td class="critical">Alert</td></tr>
    </table>
    
    <h2>Top Security Events</h2>
    <pre>
$(tail -20 /var/log/falco/falco.log | grep -E "(WARNING|ERROR|CRITICAL)")
    </pre>
    
    <h2>Recommendations</h2>
    <ul>
        <li>Review failed login attempts for potential brute force attacks</li>
        <li>Investigate privilege escalation events</li>
        <li>Update security policies if necessary</li>
    </ul>
</body>
</html>
REPORT

# レポート送信
mail -s "Security Report - $REPORT_DATE" -a "Content-Type: text/html" \
  security-team@company.com < $REPORT_FILE

echo "Security report generated: $REPORT_FILE"
EOF

chmod +x security-report.sh

# 毎日の自動実行
(crontab -l 2>/dev/null; echo "0 8 * * * /path/to/security-report.sh") | crontab -
```

### 問題97 (1点)
コンテナイメージの脆弱性スキャン結果をSlackに通知してください。

**解答例:**
```bash
cat << 'EOF' > vulnerability-notifier.sh
#!/bin/bash

IMAGE=$1
SLACK_WEBHOOK=$2

if [ -z "$IMAGE" ] || [ -z "$SLACK_WEBHOOK" ]; then
  echo "Usage: $0 <image> <slack_webhook>"
  exit 1
fi

# Trivyスキャン実行
SCAN_RESULT=$(trivy image --format json --quiet $IMAGE)
HIGH_COUNT=$(echo "$SCAN_RESULT" | jq '[.Results[]?.Vulnerabilities[]? | select(.Severity == "HIGH")] | length')
CRITICAL_COUNT=$(echo "$SCAN_RESULT" | jq '[.Results[]?.Vulnerabilities[]? | select(.Severity == "CRITICAL")] | length')

# Slack通知メッセージ構築
if [ $CRITICAL_COUNT -gt 0 ] || [ $HIGH_COUNT -gt 5 ]; then
  SEVERITY="🚨 CRITICAL"
  COLOR="danger"
elif [ $HIGH_COUNT -gt 0 ]; then
  SEVERITY="⚠️ WARNING"
  COLOR="warning"
else
  SEVERITY="✅ LOW RISK"
  COLOR="good"
fi

# Slack通知送信
curl -X POST -H 'Content-Type: application/json' \
  -d '{
    "attachments": [
      {
        "color": "'$COLOR'",
        "title": "Image Vulnerability Scan: '$IMAGE'",
        "fields": [
          {
            "title": "Severity",
            "value": "'$SEVERITY'",
            "short": true
          },
          {
            "title": "Critical",
            "value": "'$CRITICAL_COUNT'",
            "short": true
          },
          {
            "title": "High",
            "value": "'$HIGH_COUNT'",
            "short": true
          }
        ]
      }
    ]
  }' \
  $SLACK_WEBHOOK

echo "Vulnerability scan notification sent for $IMAGE"
EOF

chmod +x vulnerability-notifier.sh
```

### 問題98 (1点)
Kubernetesリソースのセキュリティ設定を監査してください。

**解答例:**
```bash
cat << 'EOF' > k8s-security-audit.sh
#!/bin/bash

echo "=== Kubernetes Security Audit ==="

# 1. Pod Security Context確認
echo "Checking Pod Security Contexts..."
kubectl get pods -A -o jsonpath='{range .items[*]}{.metadata.namespace}/{.metadata.name}: {.spec.securityContext}{"\n"}{end}' | grep -v "runAsNonRoot:true"

# 2. Service Account確認
echo "Checking Service Accounts..."
kubectl get sa -A -o jsonpath='{range .items[*]}{.metadata.namespace}/{.metadata.name}: {.automountServiceAccountToken}{"\n"}{end}' | grep -v "false"

# 3. Network Policy確認
echo "Checking Network Policies..."
NAMESPACES=$(kubectl get ns -o name | cut -d'/' -f2)
for ns in $NAMESPACES; do
  NP_COUNT=$(kubectl get networkpolicy -n $ns --no-headers 2>/dev/null | wc -l)
  if [ $NP_COUNT -eq 0 ]; then
    echo "⚠️ No Network Policy in namespace: $ns"
  fi
done

# 4. RBAC確認
echo "Checking RBAC..."
kubectl get clusterrolebinding -o jsonpath='{range .items[*]}{.metadata.name}: {.subjects[*].name}{"\n"}{end}' | grep -E "(system:anonymous|system:unauthenticated)"

# 5. Secret暗号化確認
echo "Checking Secret encryption..."
kubectl get secrets -A -o jsonpath='{range .items[*]}{.metadata.namespace}/{.metadata.name}{"\n"}{end}' | head -5

echo "=== Audit Complete ==="
EOF

chmod +x k8s-security-audit.sh
```

### 問題99 (1点)
セキュリティベンチマークスコアを自動計算してください。

**解答例:**
```bash
cat << 'EOF' > security-benchmark.sh
#!/bin/bash

# CIS Kubernetes Benchmark簡易チェック
TOTAL_CHECKS=10
PASSED_CHECKS=0

echo "=== CIS Kubernetes Benchmark Check ==="

# 1. API Server anonymous auth
if kubectl get configmap -n kube-system cluster-info -o yaml | grep -q "anonymous-auth=false"; then
  echo "✅ 1.2.1 Anonymous auth disabled"
  ((PASSED_CHECKS++))
else
  echo "❌ 1.2.1 Anonymous auth not disabled"
fi

# 2. kubelet anonymous auth
if [ -f /var/lib/kubelet/config.yaml ] && grep -q "enabled: false" /var/lib/kubelet/config.yaml; then
  echo "✅ 4.2.1 Kubelet anonymous auth disabled"
  ((PASSED_CHECKS++))
else
  echo "❌ 4.2.1 Kubelet anonymous auth not disabled"
fi

# 3. etcd encryption
if kubectl get secrets -A &>/dev/null; then
  echo "✅ 1.2.33 etcd encryption at rest enabled"
  ((PASSED_CHECKS++))
else
  echo "❌ 1.2.33 etcd encryption at rest not verified"
fi

# 4. Audit logging
if ps aux | grep kube-apiserver | grep -q "audit-log-path"; then
  echo "✅ 1.2.22 Audit logging enabled"
  ((PASSED_CHECKS++))
else
  echo "❌ 1.2.22 Audit logging not enabled"
fi

# 5. Pod Security Policy
if kubectl get psp &>/dev/null; then
  echo "✅ 5.2.1 Pod Security Policy enabled"
  ((PASSED_CHECKS++))
else
  echo "❌ 5.2.1 Pod Security Policy not enabled"
fi

# 6. Network Policy
if kubectl get networkpolicy -A --no-headers | wc -l | grep -q "^[1-9]"; then
  echo "✅ 5.3.1 Network Policy configured"
  ((PASSED_CHECKS++))
else
  echo "❌ 5.3.1 Network Policy not configured"
fi

# 7. RBAC enabled
if kubectl auth can-i --list &>/dev/null; then
  echo "✅ 5.1.1 RBAC enabled"
  ((PASSED_CHECKS++))
else
  echo "❌ 5.1.1 RBAC not verified"
fi

# 8. ServiceAccount auto mount disabled
SA_COUNT=$(kubectl get sa -A -o jsonpath='{.items[*].automountServiceAccountToken}' | tr ' ' '\n' | grep -c false)
if [ $SA_COUNT -gt 0 ]; then
  echo "✅ 5.1.5 ServiceAccount auto mount controlled"
  ((PASSED_CHECKS++))
else
  echo "❌ 5.1.5 ServiceAccount auto mount not controlled"
fi

# 9. Container security contexts
SECURE_PODS=$(kubectl get pods -A -o jsonpath='{.items[*].spec.securityContext.runAsNonRoot}' | tr ' ' '\n' | grep -c true)
if [ $SECURE_PODS -gt 0 ]; then
  echo "✅ 5.7.2 Containers run as non-root"
  ((PASSED_CHECKS++))
else
  echo "❌ 5.7.2 Containers may run as root"
fi

# 10. Secrets encryption
if kubectl get secret -n kube-system | grep -q encryption; then
  echo "✅ Secrets properly encrypted"
  ((PASSED_CHECKS++))
else
  echo "❌ Secrets encryption not verified"
fi

# スコア計算
SCORE=$((PASSED_CHECKS * 100 / TOTAL_CHECKS))
echo "=== Benchmark Score: $SCORE% ($PASSED_CHECKS/$TOTAL_CHECKS) ==="

if [ $SCORE -ge 80 ]; then
  echo "🎉 Excellent security posture"
elif [ $SCORE -ge 60 ]; then
  echo "⚠️ Good security posture, room for improvement"
else
  echo "🚨 Poor security posture, immediate action required"
fi
EOF

chmod +x security-benchmark.sh
```

### 問題100 (1点)
最終的なセキュリティ評価レポートを生成してください。

**解答例:**
```bash
cat << 'EOF' > final-security-assessment.sh
#!/bin/bash

OUTPUT_FILE="/tmp/final-security-assessment-$(date +%Y%m%d).json"

cat << ASSESSMENT > $OUTPUT_FILE
{
  "assessment_date": "$(date -Iseconds)",
  "cluster_info": {
    "cluster_version": "$(kubectl version --short --client)",
    "node_count": $(kubectl get nodes --no-headers | wc -l),
    "namespace_count": $(kubectl get ns --no-headers | wc -l)
  },
  "security_status": {
    "authentication": {
      "anonymous_auth_disabled": $(ps aux | grep kube-apiserver | grep -q "anonymous-auth=false" && echo true || echo false),
      "rbac_enabled": $(kubectl auth can-i --list &>/dev/null && echo true || echo false)
    },
    "authorization": {
      "pod_security_policy": $(kubectl get psp &>/dev/null && echo true || echo false),
      "network_policy_count": $(kubectl get networkpolicy -A --no-headers | wc -l)
    },
    "encryption": {
      "etcd_encryption": $(kubectl get secrets -A &>/dev/null && echo true || echo false),
      "tls_enabled": true
    },
    "monitoring": {
      "audit_logging": $(ps aux | grep kube-apiserver | grep -q "audit-log-path" && echo true || echo false),
      "falco_installed": $(systemctl is-active falco &>/dev/null && echo true || echo false)
    }
  },
  "compliance_score": {
    "cis_benchmark": "$(./security-benchmark.sh | grep 'Benchmark Score' | grep -o '[0-9]*')",
    "security_grade": "$([ $(./security-benchmark.sh | grep 'Benchmark Score' | grep -o '[0-9]*') -ge 80 ] && echo 'A' || echo 'B')"
  },
  "recommendations": [
    "Enable Pod Security Standards",
    "Implement comprehensive Network Policies",
    "Configure Falco for runtime security",
    "Set up centralized logging with encryption",
    "Regular security policy updates"
  ],
  "next_assessment": "$(date -d '+30 days' -Iseconds)"
}
ASSESSMENT

echo "Final security assessment saved to: $OUTPUT_FILE"

# 結果をSlackに送信
SCORE=$(jq -r '.compliance_score.cis_benchmark' $OUTPUT_FILE)
GRADE=$(jq -r '.compliance_score.security_grade' $OUTPUT_FILE)

curl -X POST -H 'Content-Type: application/json' \
  -d '{
    "text": "Security Assessment Complete",
    "attachments": [
      {
        "color": "'$([ "$GRADE" = "A" ] && echo "good" || echo "warning")'",
        "fields": [
          {
            "title": "Compliance Score",
            "value": "'$SCORE'%",
            "short": true
          },
          {
            "title": "Security Grade",
            "value": "'$GRADE'",
            "short": true
          }
        ]
      }
    ]
  }' \
  $SLACK_WEBHOOK_URL

echo "Assessment notification sent"
EOF

chmod +x final-security-assessment.sh
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