# Certified Kubernetes Security Specialist (CKS) 試験対策のポイント

## 🎯 試験概要と戦略

### 試験の特徴
- **100%実技試験**: 理論問題なし、全て実装・設定作業
- **制限時間**: 120分で15-20問（問題あたり6-8分）
- **Remote Desktop**: ブラウザベースの仮想環境
- **複数クラスター**: 異なる設定の複数クラスター間で作業

### 効果的な時間配分
```
作業時間配分:
├── 環境確認・準備: 5分
├── 簡単な問題: 40分 (8問 × 5分)
├── 中程度の問題: 50分 (7問 × 7分)
├── 難問: 20分 (3問 × 7分程度)
└── 見直し・仕上げ: 5分
```

## 📋 ドメイン別対策

### Cluster Setup (10%)

#### 頻出トピック
1. **API Server セキュリティ設定**
   - TLS設定
   - Admission controllers
   - Audit logging

2. **etcd暗号化**
   - Encryption at rest
   - Encryption configuration

3. **kubelet セキュリティ**
   - Anonymous auth無効化
   - Authorization mode設定

#### 重要な設定ファイル
```yaml
# /etc/kubernetes/manifests/kube-apiserver.yaml
apiVersion: v1
kind: Pod
spec:
  containers:
  - name: kube-apiserver
    command:
    - kube-apiserver
    - --enable-admission-plugins=PodSecurityPolicy,NodeRestriction
    - --audit-log-path=/var/log/apiserver-audit.log
    - --audit-policy-file=/etc/kubernetes/audit-policy.yaml
    - --encryption-provider-config=/etc/kubernetes/encryption-config.yaml
```

#### よくある作業パターン
```bash
# API Server設定変更
sudo vi /etc/kubernetes/manifests/kube-apiserver.yaml
# 設定反映確認
kubectl get pods -n kube-system | grep apiserver

# etcd暗号化設定
sudo vi /etc/kubernetes/encryption-config.yaml
# 暗号化適用
kubectl get secrets --all-namespaces -o json | kubectl replace -f -
```

### Cluster Hardening (15%)

#### 頻出トピック
1. **RBAC設定**
   - Role/ClusterRole作成
   - RoleBinding/ClusterRoleBinding
   - ServiceAccount セキュリティ

2. **Network Policies**
   - Ingress/Egress rules
   - Label selector活用
   - Default deny policies

3. **CIS Benchmarks**
   - kube-bench実行
   - 推奨設定の適用

#### RBAC設定例
```yaml
# Role作成
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  namespace: production
  name: pod-reader
rules:
- apiGroups: [""]
  resources: ["pods"]
  verbs: ["get", "watch", "list"]

---
# RoleBinding作成
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: read-pods
  namespace: production
subjects:
- kind: User
  name: jane
  apiGroup: rbac.authorization.k8s.io
roleRef:
  kind: Role
  name: pod-reader
  apiGroup: rbac.authorization.k8s.io
```

#### Network Policy例
```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: deny-all
  namespace: production
spec:
  podSelector: {}
  policyTypes:
  - Ingress
  - Egress
  # 明示的にルールを指定しない = 全拒否
```

### System Hardening (15%)

#### 頻出トピック
1. **AppArmor設定**
   - Profile作成・適用
   - Pod annotation設定

2. **seccomp設定**
   - Profile作成
   - Pod securityContext設定

3. **Linux セキュリティ**
   - ファイル権限設定
   - Service無効化

#### AppArmor設定例
```bash
# AppArmor profile作成
sudo vi /etc/apparmor.d/docker-deny-write
# Profile内容例:
profile docker-deny-write flags=(attach_disconnected,mediate_deleted) {
  file,
  deny /etc/** w,
  deny /sys/** w,
}

# Profile読み込み
sudo apparmor_parser -r /etc/apparmor.d/docker-deny-write

# Pod設定
metadata:
  annotations:
    container.apparmor.security.beta.kubernetes.io/nginx: localhost/docker-deny-write
```

#### seccomp設定例
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: secure-pod
spec:
  securityContext:
    seccompProfile:
      type: Localhost
      localhostProfile: custom-profile.json
  containers:
  - name: nginx
    image: nginx
```

### Minimize Microservice Vulnerabilities (20%)

#### 頻出トピック
1. **Pod Security Standards**
   - restricted, baseline, privileged
   - Pod Security admission controller

2. **Security Context**
   - runAsUser, runAsGroup
   - allowPrivilegeEscalation: false
   - readOnlyRootFilesystem: true

3. **Admission Controllers**
   - OPA Gatekeeper
   - Pod Security Policy (deprecated)

#### セキュアなPod設定
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: secure-pod
spec:
  securityContext:
    runAsUser: 1000
    runAsGroup: 1000
    runAsNonRoot: true
    fsGroup: 1000
  containers:
  - name: nginx
    image: nginx:1.20
    securityContext:
      allowPrivilegeEscalation: false
      readOnlyRootFilesystem: true
      runAsNonRoot: true
      capabilities:
        drop:
        - ALL
    volumeMounts:
    - name: tmp
      mountPath: /tmp
    - name: var-cache-nginx
      mountPath: /var/cache/nginx
  volumes:
  - name: tmp
    emptyDir: {}
  - name: var-cache-nginx
    emptyDir: {}
```

### Supply Chain Security (20%)

#### 頻出トピック
1. **Image scanning**
   - trivy, Clair使用
   - Admission controller統合

2. **Image signing**
   - Cosign使用
   - Policy設定

3. **Admission Controllers**
   - ImagePolicyWebhook
   - OPA Gatekeeper policies

#### Image scanning例
```bash
# trivy でimage scan
trivy image nginx:latest

# 脆弱性のあるimageの確認
kubectl get pods -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.spec.containers[*].image}{"\n"}{end}'
```

#### OPA Gatekeeper policy例
```yaml
apiVersion: templates.gatekeeper.sh/v1beta1
kind: ConstraintTemplate
metadata:
  name: k8srequirelabels
spec:
  crd:
    spec:
      names:
        kind: K8sRequireLabels
      validation:
        properties:
          labels:
            type: array
            items:
              type: string
  targets:
    - target: admission.k8s.gatekeeper.sh
      rego: |
        package k8srequirelabels
        violation[{"msg": msg}] {
          required := input.parameters.labels
          provided := input.review.object.metadata.labels
          missing := required[_]
          not provided[missing]
          msg := sprintf("Missing required label: %v", [missing])
        }
```

### Monitoring, Logging and Runtime Security (20%)

#### 頻出トピック
1. **Falco監視**
   - Rule設定
   - Alert設定
   - カスタムルール

2. **Audit logging**
   - Audit policy設定
   - ログ分析

3. **Runtime security**
   - 異常検知
   - Incident response

#### Falco設定例
```yaml
# /etc/falco/falco_rules.local.yaml
- rule: Detect Shell in Container
  desc: Alert if a shell is opened in a container
  condition: >
    spawned_process and container and
    (proc.name in (shell_binaries) or
     proc.name in (python_binaries) or
     proc.name in (node_binaries))
  output: >
    Shell opened in container (user=%user.name container_id=%container.id 
    container_name=%container.name image=%container.image.repository:%container.image.tag 
    proc=%proc.cmdline)
  priority: WARNING
```

## 🔧 実技試験テクニック

### 効率的な作業方法

#### 1. 環境確認の高速化
```bash
# 現在のcontext確認
kubectl config current-context

# 利用可能なクラスター一覧
kubectl config get-contexts

# クラスター切り替え
kubectl config use-context cluster-name

# Node情報確認
kubectl get nodes -o wide
```

#### 2. YAML作成の効率化
```bash
# Dry-runでYAML生成
kubectl create role developer --verb=create --verb=get --verb=list --verb=update --verb=delete --resource=pods --dry-run=client -o yaml

# 既存リソースからYAML出力
kubectl get networkpolicy -o yaml > backup.yaml

# YAML即座編集
kubectl edit networkpolicy my-policy
```

#### 3. トラブルシューティング
```bash
# Pod詳細確認
kubectl describe pod problematic-pod

# ログ確認
kubectl logs -f pod-name --previous

# Events確認
kubectl get events --sort-by=.metadata.creationTimestamp

# Security context確認
kubectl get pod -o jsonpath='{.spec.securityContext}'
```

### よくある落とし穴と対策

#### 1. RBAC設定ミス
- ❌ 広すぎる権限設定
- ✅ 最小権限の原則
- ❌ apiGroups指定忘れ
- ✅ 正確なリソース・動詞指定

#### 2. Network Policy設定ミス
- ❌ podSelectorの誤設定
- ✅ 正確なラベル選択
- ❌ port指定忘れ
- ✅ protocol, port の明確な指定

#### 3. Security Context設定ミス
- ❌ privileged: true のまま
- ✅ 必要最小限の権限
- ❌ runAsRoot: true
- ✅ runAsNonRoot: true

## 📚 試験当日の準備

### 前日チェックリスト
- [ ] 試験環境の接続テスト
- [ ] kubectl コマンドの総復習
- [ ] 重要なYAMLマニフェストの確認
- [ ] 時間配分の最終確認

### 当日の心構え
- [ ] 落ち着いて問題文を正確に読む
- [ ] 作業後は必ず検証する
- [ ] 分からない問題は後回しにする
- [ ] 時間配分を常に意識する

### 必須コマンド集
```bash
# 基本操作
kubectl get/describe/edit/delete
kubectl apply/create -f
kubectl config use-context

# セキュリティ関連
kubectl auth can-i
kubectl get rolebindings/clusterrolebindings
kubectl get networkpolicies
kubectl get psp (deprecated)

# トラブルシューティング
kubectl logs
kubectl get events
kubectl describe
```

## 🎯 合格のための最終アドバイス

### 実践力の重要性
- 単なる暗記ではなく実際の操作経験
- 制限時間内での作業スピード
- エラー対応・トラブルシューティング能力
- セキュリティベストプラクティスの理解

### 学習方法のコツ
1. **実環境での練習**: 実際のクラスター環境
2. **制限時間を意識**: 常にタイマーを使用
3. **コマンド暗記**: よく使うコマンドは暗記
4. **ドキュメント活用**: 試験中も参照可能

### 試験当日の戦略
- **簡単な問題から**: 確実に点数を取る
- **検証を忘れずに**: 設定後は動作確認
- **時間管理**: 1問に時間をかけすぎない
- **冷静な判断**: パニックにならない

---

**頑張れ！** CKSはKubernetesセキュリティの実践力を証明する最高レベルの資格です。あなたの努力と経験が必ず合格につながります。セキュリティエキスパートとしての価値ある認定を目指して頑張ってください！