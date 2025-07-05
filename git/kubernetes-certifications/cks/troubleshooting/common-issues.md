# CKS - よくある問題と解決策

## 📋 概要

CKS試験とKubernetesセキュリティ実務でよく遭遇する問題とその解決策をまとめています。実技試験での効率的なセキュリティトラブルシューティング手順も含めて解説します。

## 🚨 Domain 1: Cluster Setup - クラスターセットアップ関連

### 問題1: etcd暗号化設定が機能しない

#### 症状
```bash
kubectl get secrets -A
# 平文でデータが保存されている
etcdctl get /registry/secrets/default/my-secret --print-value-only
```

#### 原因分析
- 暗号化設定ファイルの形式エラー
- API Server の設定不備
- 暗号化キーの問題

#### 解決手順
```bash
# 1. 暗号化設定ファイル作成
cat > /etc/kubernetes/encryption-config.yaml << EOF
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

# 2. API Server 設定更新
sudo vim /etc/kubernetes/manifests/kube-apiserver.yaml
# 以下を追加
spec:
  containers:
  - command:
    - kube-apiserver
    - --encryption-provider-config=/etc/kubernetes/encryption-config.yaml
    volumeMounts:
    - name: encryption-config
      mountPath: /etc/kubernetes/encryption-config.yaml
      readOnly: true
  volumes:
  - name: encryption-config
    hostPath:
      path: /etc/kubernetes/encryption-config.yaml
      type: File

# 3. 既存secretの再暗号化
kubectl get secrets --all-namespaces -o json | kubectl replace -f -

# 4. 検証
sudo ETCDCTL_API=3 etcdctl \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key \
  get /registry/secrets/default/my-secret
```

### 問題2: kubelet のセキュリティ設定が不適切

#### 症状
- 匿名アクセスが有効
- 認証なしでkubelet APIにアクセス可能

#### 解決手順
```bash
# 1. kubelet設定確認
sudo cat /var/lib/kubelet/config.yaml

# 2. セキュア設定への修正
sudo vim /var/lib/kubelet/config.yaml
```

```yaml
# セキュアなkubelet設定
apiVersion: kubelet.config.k8s.io/v1beta1
kind: KubeletConfiguration
authentication:
  anonymous:
    enabled: false  # 匿名アクセス無効化
  webhook:
    enabled: true   # Webhook認証有効化
authorization:
  mode: Webhook     # 認可モード設定
readOnlyPort: 0     # 読み取り専用ポート無効化
serverTLSBootstrap: true
rotateCertificates: true
```

```bash
# 3. kubelet再起動
sudo systemctl restart kubelet

# 4. 検証
curl -k https://node-ip:10250/pods
# 401 Unauthorized が返されることを確認
```

## 🔒 Domain 2: Cluster Hardening - クラスター堅牢化関連

### 問題3: RBAC設定が正しく動作しない

#### 症状
```bash
kubectl auth can-i get pods --as=system:serviceaccount:default:test
# 期待と異なる結果が返される
```

#### 解決手順
```bash
# 1. 現在のRBAC設定確認
kubectl get clusterroles,roles,clusterrolebindings,rolebindings -A

# 2. Service Account の権限確認
kubectl auth can-i --list --as=system:serviceaccount:default:test

# 3. 正しいRBAC設定例
cat << EOF | kubectl apply -f -
apiVersion: v1
kind: ServiceAccount
metadata:
  name: limited-sa
  namespace: default
---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  namespace: default
  name: pod-reader
rules:
- apiGroups: [""]
  resources: ["pods"]
  verbs: ["get", "list"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: read-pods
  namespace: default
subjects:
- kind: ServiceAccount
  name: limited-sa
  namespace: default
roleRef:
  kind: Role
  name: pod-reader
  apiGroup: rbac.authorization.k8s.io
EOF

# 4. 検証
kubectl auth can-i get pods --as=system:serviceaccount:default:limited-sa
kubectl auth can-i create pods --as=system:serviceaccount:default:limited-sa
```

### 問題4: Network Policy が期待通りに動作しない

#### 症状
- ポッド間通信が遮断されない
- 外部通信が制御されない

#### 解決手順
```bash
# 1. CNI プラグインがNetwork Policyをサポートしているか確認
kubectl get pods -n kube-system | grep -E "(calico|cilium|weave)"

# 2. 現在のNetwork Policy確認
kubectl get networkpolicies -A

# 3. テスト用Podを作成
kubectl run test-pod --image=busybox --rm -it -- sh
# 別のターミナルで
kubectl run target-pod --image=nginx --labels="app=target"

# 4. 正しいNetwork Policy例
cat << EOF | kubectl apply -f -
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: deny-all-ingress
  namespace: default
spec:
  podSelector: {}
  policyTypes:
  - Ingress
---
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-specific-ingress
  namespace: default
spec:
  podSelector:
    matchLabels:
      app: target
  policyTypes:
  - Ingress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: allowed
    ports:
    - protocol: TCP
      port: 80
EOF

# 5. 検証
kubectl label pod test-pod app=allowed
kubectl exec test-pod -- wget -qO- target-pod-ip
# 成功することを確認

kubectl label pod test-pod app-
kubectl exec test-pod -- wget -qO- target-pod-ip
# タイムアウトすることを確認
```

## 🛡️ Domain 3: System Hardening - システム堅牢化関連

### 問題5: AppArmor プロファイルが読み込まれない

#### 症状
```bash
sudo aa-status
# 期待するプロファイルが表示されない
```

#### 解決手順
```bash
# 1. AppArmor の状態確認
sudo systemctl status apparmor
sudo aa-status

# 2. カスタムプロファイル作成
sudo vim /etc/apparmor.d/k8s-nginx
```

```bash
# AppArmor プロファイル例
#include <tunables/global>

/usr/sbin/nginx flags=(attach_disconnected,mediate_deleted) {
  #include <abstractions/base>
  #include <abstractions/nameservice>

  capability dac_override,
  capability setuid,
  capability setgid,

  /usr/sbin/nginx mr,
  /etc/nginx/ r,
  /etc/nginx/** r,
  /var/log/nginx/ rw,
  /var/log/nginx/** rw,
  /var/cache/nginx/ rw,
  /var/cache/nginx/** rw,
  /run/nginx.pid rw,

  deny /proc/sys/kernel/** wklx,
  deny /sys/kernel/security/** rwklx,
}
```

```bash
# 3. プロファイル読み込み
sudo apparmor_parser -r /etc/apparmor.d/k8s-nginx

# 4. Pod でAppArmorプロファイル使用
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
    securityContext:
      allowPrivilegeEscalation: false
EOF

# 5. 検証
kubectl exec nginx-apparmor -- cat /proc/1/attr/current
# k8s-nginx (enforce) が表示されることを確認
```

### 問題6: Seccomp プロファイルが適用されない

#### 症状
- Pod でSystemcallが制限されない
- セキュリティコンテキストの設定ミス

#### 解決手順
```bash
# 1. カスタムSeccompプロファイル作成
sudo mkdir -p /var/lib/kubelet/seccomp/profiles
sudo vim /var/lib/kubelet/seccomp/profiles/custom-profile.json
```

```json
{
  "defaultAction": "SCMP_ACT_ERRNO",
  "architectures": ["SCMP_ARCH_X86_64"],
  "syscalls": [
    {
      "names": [
        "accept4",
        "arch_prctl",
        "bind",
        "brk",
        "close",
        "connect",
        "dup2",
        "epoll_create1",
        "epoll_ctl",
        "epoll_wait",
        "exit",
        "exit_group",
        "fchown",
        "fcntl",
        "fstat",
        "futex",
        "getdents64",
        "getpid",
        "getuid",
        "listen",
        "mmap",
        "munmap",
        "nanosleep",
        "openat",
        "poll",
        "read",
        "rt_sigaction",
        "rt_sigprocmask",
        "rt_sigreturn",
        "sendto",
        "set_robust_list",
        "setgid",
        "setgroups",
        "setuid",
        "socket",
        "write"
      ],
      "action": "SCMP_ACT_ALLOW"
    }
  ]
}
```

```bash
# 2. Pod でSeccompプロファイル使用
cat << EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: secure-pod
spec:
  securityContext:
    seccompProfile:
      type: Localhost
      localhostProfile: profiles/custom-profile.json
  containers:
  - name: app
    image: busybox
    command: ["sleep", "3600"]
    securityContext:
      allowPrivilegeEscalation: false
      runAsNonRoot: true
      runAsUser: 1000
      capabilities:
        drop:
        - ALL
EOF

# 3. 検証
kubectl exec secure-pod -- ls /proc/1/
# 制限されたsyscallで失敗することを確認
```

## 🔍 Domain 4: Minimize Microservice Vulnerabilities

### 問題7: Pod Security Standards が適用されない

#### 症状
- 特権Podが作成できてしまう
- セキュリティポリシーが機能しない

#### 解決手順
```bash
# 1. 名前空間にPod Security Standards設定
kubectl label namespace default \
  pod-security.kubernetes.io/enforce=restricted \
  pod-security.kubernetes.io/audit=restricted \
  pod-security.kubernetes.io/warn=restricted

# 2. 違反するPodの作成テスト
cat << EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: privileged-pod
spec:
  containers:
  - name: app
    image: nginx
    securityContext:
      privileged: true  # これは拒否される
EOF

# 3. 準拠するPodの作成
cat << EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: compliant-pod
spec:
  securityContext:
    runAsNonRoot: true
    runAsUser: 1000
    fsGroup: 2000
    seccompProfile:
      type: RuntimeDefault
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

### 問題8: OPA Gatekeeper のポリシーが動作しない

#### 症状
- 制約テンプレートが適用されない
- ポリシー違反が検出されない

#### 解決手順
```bash
# 1. Gatekeeper のインストール確認
kubectl get pods -n gatekeeper-system

# 2. 制約テンプレート作成
cat << EOF | kubectl apply -f -
apiVersion: templates.gatekeeper.sh/v1beta1
kind: ConstraintTemplate
metadata:
  name: requiredlabels
spec:
  crd:
    spec:
      names:
        kind: RequiredLabels
      validation:
        type: object
        properties:
          labels:
            type: array
            items:
              type: string
  targets:
    - target: admission.k8s.gatekeeper.sh
      rego: |
        package requiredlabels

        violation[{"msg": msg}] {
          required := input.parameters.labels
          provided := input.review.object.metadata.labels
          missing := required[_]
          not provided[missing]
          msg := sprintf("You must provide labels: %v", [missing])
        }
EOF

# 3. 制約作成
cat << EOF | kubectl apply -f -
apiVersion: constraints.gatekeeper.sh/v1beta1
kind: RequiredLabels
metadata:
  name: must-have-environment
spec:
  match:
    kinds:
      - apiGroups: [""]
        kinds: ["Pod"]
  parameters:
    labels: ["environment"]
EOF

# 4. 検証
kubectl run test-pod --image=nginx
# 拒否されることを確認

kubectl run test-pod --image=nginx --labels="environment=test"
# 成功することを確認
```

## 🔎 Domain 5: Supply Chain Security

### 問題9: Image scanning が機能しない

#### 症状
- 脆弱性のあるイメージがデプロイされる
- Admission Controller が動作しない

#### 解決手順
```bash
# 1. Trivy によるイメージスキャン
trivy image nginx:latest
trivy image --severity HIGH,CRITICAL nginx:latest

# 2. Admission Controller でのイメージスキャン
cat << EOF | kubectl apply -f -
apiVersion: v1
kind: ConfigMap
metadata:
  name: image-scan-policy
  namespace: default
data:
  policy.rego: |
    package kubernetes.admission
    
    deny[msg] {
      input.request.kind.kind == "Pod"
      image := input.request.object.spec.containers[_].image
      not image_allowed(image)
      msg := sprintf("Image %v has not been scanned or has vulnerabilities", [image])
    }
    
    image_allowed(image) {
      # 許可されたレジストリからのイメージのみ許可
      startswith(image, "registry.company.com/")
    }
    
    image_allowed(image) {
      # スキャン済みイメージリストに含まれている
      scanned_images := ["nginx:1.21", "busybox:1.35"]
      image in scanned_images
    }
EOF

# 3. ValidatingAdmissionWebhook設定
# (実際の実装は複雑なため、概念的な例)
```

### 問題10: Image signing verification が失敗する

#### 症状
- 署名されていないイメージがデプロイされる
- cosign verification エラー

#### 解決手順
```bash
# 1. cosign のインストール
curl -O -L "https://github.com/sigstore/cosign/releases/latest/download/cosign-linux-amd64"
sudo mv cosign-linux-amd64 /usr/local/bin/cosign
sudo chmod +x /usr/local/bin/cosign

# 2. イメージの署名確認
cosign verify --key cosign.pub registry.company.com/myapp:v1.0

# 3. Admission Controller での署名検証
cat << EOF | kubectl apply -f -
apiVersion: v1
kind: ConfigMap
metadata:
  name: cosign-policy
data:
  policy.yaml: |
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
            MFkwEwYHKoZIzj0CAQYIKoZIzj0DAQcDQgAE...
            -----END PUBLIC KEY-----
EOF
```

## 🔍 Domain 6: Monitoring, Logging and Runtime Security

### 問題11: Falco が期待するアラートを生成しない

#### 症状
- 不審な活動が検出されない
- Falco ルールが動作しない

#### 解決手順
```bash
# 1. Falco の状態確認
sudo systemctl status falco
sudo journalctl -u falco -f

# 2. カスタムルール作成
sudo vim /etc/falco/falco_rules.local.yaml
```

```yaml
# カスタムFalcoルール
- rule: Suspicious Shell Activity
  desc: Detect shell activity in containers
  condition: >
    spawned_process and
    container and
    proc.name in (sh, bash, zsh, fish) and
    not proc.pname in (kubelet, dockerd)
  output: >
    Shell spawned in container (user=%user.name container_id=%container.id 
    container_name=%container.name shell=%proc.name parent=%proc.pname 
    cmdline=%proc.cmdline)
  priority: WARNING
  tags: [shell, container]

- rule: Sensitive File Access
  desc: Detect access to sensitive files
  condition: >
    open_read and
    container and
    fd.name in (/etc/passwd, /etc/shadow, /etc/ssh/sshd_config)
  output: >
    Sensitive file accessed (user=%user.name container_id=%container.id 
    file=%fd.name proc=%proc.name cmdline=%proc.cmdline)
  priority: HIGH
  tags: [filesystem, sensitive]
```

```bash
# 3. Falco 再起動
sudo systemctl restart falco

# 4. テスト
kubectl exec -it test-pod -- /bin/bash
# Falco アラートが生成されることを確認
```

### 問題12: Audit logging が設定されていない

#### 症状
- API Server のアクティビティが記録されない
- セキュリティイベントが追跡できない

#### 解決手順
```bash
# 1. Audit Policy 作成
sudo vim /etc/kubernetes/audit-policy.yaml
```

```yaml
apiVersion: audit.k8s.io/v1
kind: Policy
rules:
- level: Metadata
  namespaces: ["kube-system", "kube-public", "kube-node-lease"]
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
  omitStages:
  - RequestReceived
```

```bash
# 2. API Server 設定更新
sudo vim /etc/kubernetes/manifests/kube-apiserver.yaml
# 以下を追加
spec:
  containers:
  - command:
    - kube-apiserver
    - --audit-log-path=/var/log/audit.log
    - --audit-policy-file=/etc/kubernetes/audit-policy.yaml
    - --audit-log-maxage=30
    - --audit-log-maxbackup=3
    - --audit-log-maxsize=100
    volumeMounts:
    - name: audit-policy
      mountPath: /etc/kubernetes/audit-policy.yaml
      readOnly: true
    - name: audit-log
      mountPath: /var/log/audit.log
  volumes:
  - name: audit-policy
    hostPath:
      path: /etc/kubernetes/audit-policy.yaml
      type: File
  - name: audit-log
    hostPath:
      path: /var/log/audit.log
      type: FileOrCreate

# 3. 検証
sudo tail -f /var/log/audit.log
# API アクティビティが記録されることを確認
```

## 🛠️ 試験対策のための効率的デバッグ

### 高速診断コマンド集

```bash
# セキュリティ状態の総合確認
alias k=kubectl
alias kgsec='kubectl get secrets,serviceaccounts,roles,rolebindings,clusterroles,clusterrolebindings'

# Pod セキュリティコンテキスト確認
k get pod -o custom-columns="NAME:.metadata.name,SECURITY:.spec.securityContext"

# Network Policy 確認
k get networkpolicy -A

# RBAC 権限確認
k auth can-i --list --as=system:serviceaccount:default:my-sa

# ノードセキュリティ確認
k get nodes -o custom-columns="NAME:.metadata.name,KERNEL:.status.nodeInfo.kernelVersion,KUBELET:.status.nodeInfo.kubeletVersion"
```

### セキュリティ検証の自動化

```bash
# セキュリティチェックスクリプト
#!/bin/bash
echo "=== Kubernetes Security Check ==="

echo "1. Checking etcd encryption..."
sudo ETCDCTL_API=3 etcdctl --endpoints=127.0.0.1:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key \
  get /registry/secrets/default/test-secret | grep -q "k8s:enc:aescbc" && echo "✓ Encrypted" || echo "✗ Not encrypted"

echo "2. Checking anonymous access..."
curl -k https://localhost:6443/api/v1/namespaces 2>/dev/null | grep -q "Unauthorized" && echo "✓ Anonymous access disabled" || echo "✗ Anonymous access enabled"

echo "3. Checking Pod Security Standards..."
kubectl get ns default -o jsonpath='{.metadata.labels}' | grep -q "pod-security" && echo "✓ Pod Security Standards enabled" || echo "✗ Pod Security Standards not configured"

echo "4. Checking Network Policies..."
kubectl get networkpolicy -A --no-headers | wc -l | awk '{if($1>0) print "✓ Network Policies found: " $1; else print "✗ No Network Policies"}'

echo "5. Checking RBAC..."
kubectl get clusterrolebinding system:anonymous 2>/dev/null && echo "✗ Anonymous ClusterRoleBinding exists" || echo "✓ No anonymous ClusterRoleBinding"
```

## 📚 予防策とベストプラクティス

### 1. Defense in Depth
- 複数レイヤーでのセキュリティ対策
- 最小権限の原則の徹底
- 定期的なセキュリティ監査

### 2. 継続的監視
- Falco による runtime monitoring
- Audit logs の分析
- Network traffic の監視

### 3. セキュアな設定管理
- CIS Benchmarks の適用
- セキュリティポリシーの自動化
- Infrastructure as Code

### 4. インシデント対応
- セキュリティイベントの対応手順
- ログ分析とフォレンジック
- 迅速な復旧手順

---

**重要**: CKS試験では制限時間内でのセキュリティ実装が求められます。基本的なセキュリティ設定を迅速に実行できるよう、コマンドとYAMLテンプレートを習熟することが合格の鍵です。