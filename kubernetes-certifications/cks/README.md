# Certified Kubernetes Security Specialist (CKS)

## 📋 試験概要

**正式名称**: Certified Kubernetes Security Specialist  
**試験コード**: CKS  
**難易度**: ⭐⭐⭐⭐⭐  
**試験時間**: 120分  
**問題数**: 15-20問（実技試験）  
**費用**: $395 USD  
**合格点**: 67%  

### 📊 試験ドメインと配点

1. **Cluster Setup (10%)** - クラスターのセキュアな設定
2. **Cluster Hardening (15%)** - クラスターの堅牢化
3. **System Hardening (15%)** - システムレベルのセキュリティ
4. **Minimize Microservice Vulnerabilities (20%)** - マイクロサービスの脆弱性最小化
5. **Supply Chain Security (20%)** - サプライチェーンセキュリティ
6. **Monitoring, Logging and Runtime Security (20%)** - 監視・ログ・ランタイムセキュリティ

## 🎯 対象者

- **推奨経験**: CKA保有者、Kubernetesセキュリティ実務経験
- **前提資格**: CKA (Certified Kubernetes Administrator) **必須**
- **実務経験**: Kubernetesセキュリティ実装経験

### 必要なスキル
- Kubernetesクラスター管理
- コンテナセキュリティ
- ネットワークセキュリティ
- システムセキュリティ
- セキュリティ監視・分析

## 🗂️ 教材構成

### 📚 基礎教材
- `00-fundamentals.md` - Kubernetesセキュリティ基礎
- `exam-tips.md` - 試験対策のポイント

### 🔬 ハンズオンラボ
- `labs/lab01-cluster-security-foundation/` - クラスターセキュリティ基盤
- `labs/lab02-cluster-hardening/` - クラスター堅牢化
- `labs/lab03-system-hardening/` - システム堅牢化
- `labs/lab04-microservice-security/` - マイクロサービスセキュリティ
- `labs/lab05-supply-chain-security/` - サプライチェーンセキュリティ
- `labs/lab06-monitoring-runtime-security/` - 監視・ランタイムセキュリティ

### 📝 問題演習
- `practice-exams/` - 実技想定問題集（100問）
- `troubleshooting/` - セキュリティトラブルシューティング

## 🚀 学習順序（推奨）

### Phase 1: 基礎固め（2-3週間）
1. **Kubernetesセキュリティ概論**
   - セキュリティアーキテクチャ
   - 脅威モデル
   - Defense in Depth

2. **クラスターセキュリティ基盤**
   - RBAC設定
   - Network Policies
   - Pod Security Standards

### Phase 2: 堅牢化実装（4-5週間）
3. **Lab 1: クラスターセキュリティ基盤**
   - API Server セキュリティ
   - etcd暗号化
   - kubelet設定

4. **Lab 2: クラスター堅牢化**
   - CIS Benchmarks適用
   - Node セキュリティ
   - Network segmentation

### Phase 3: システムセキュリティ（3-4週間）
5. **Lab 3: システム堅牢化**
   - Linux セキュリティ
   - AppArmor/SELinux
   - Seccomp profiles

6. **Lab 4: マイクロサービスセキュリティ**
   - Pod Security Context
   - Service Mesh セキュリティ
   - Admission Controllers

### Phase 4: 高度なセキュリティ（3-4週間）
7. **Lab 5: サプライチェーンセキュリティ**
   - Image scanning
   - Image signing
   - Supply chain attacks対策

8. **Lab 6: 監視・ランタイムセキュリティ**
   - Falco による監視
   - Audit logging
   - Runtime security

### Phase 5: 試験対策（1-2週間）
9. **実技問題演習**
   - 制限時間内での作業
   - トラブルシューティング
   - 実環境での検証

## 💰 費用概算

### 学習環境構築コスト
| 項目 | 推定コスト |
|------|------------|
| Cloud環境 (3ヶ月) | $100-150 |
| 練習用クラスター | $50-80 |
| 試験受験料 | $395 |
| 再試験（必要時） | $395 |

**総計**: $545-625

### コスト削減のコツ
- ローカル環境でのminikube/kind使用
- 学習後はクラウドリソース即座削除
- 無料のKubernetes学習リソース活用

## 🛠️ 事前準備

### 必要な環境
```bash
# kubectl インストール
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
chmod +x kubectl
sudo mv kubectl /usr/local/bin/

# Docker インストール
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# kind インストール (ローカル検証用)
go install sigs.k8s.io/kind@v0.20.0
```

### 必要な知識
- **CKA取得済み**: 必須前提条件
- **Linux システム管理**: 中級レベル
- **コンテナセキュリティ**: 基礎知識
- **ネットワークセキュリティ**: 基礎知識

## 📊 学習進捗管理

### ドメイン別チェックリスト

#### Cluster Setup (10%)
- [ ] TLS証明書の理解と設定
- [ ] API Server セキュリティ設定
- [ ] etcd暗号化設定
- [ ] kubelet セキュリティ設定

#### Cluster Hardening (15%)
- [ ] RBAC設定と最小権限原則
- [ ] Service Account セキュリティ
- [ ] Network Policies実装
- [ ] CIS Benchmarks適用

#### System Hardening (15%)
- [ ] Linux セキュリティ基礎
- [ ] AppArmor/SELinux設定
- [ ] Seccomp profiles
- [ ] システム監査設定

#### Minimize Microservice Vulnerabilities (20%)
- [ ] Pod Security Standards
- [ ] Security Context設定
- [ ] Admission Controllers
- [ ] OPA Gatekeeper

#### Supply Chain Security (20%)
- [ ] Image vulnerability scanning
- [ ] Image signing and verification
- [ ] Secure image repositories
- [ ] Binary authorization

#### Monitoring, Logging and Runtime Security (20%)
- [ ] Falco による runtime monitoring
- [ ] Audit logging設定
- [ ] Intrusion detection
- [ ] Incident response

## 🎯 試験対策のポイント

### 頻出トピック
1. **RBAC設定**: Role, ClusterRole, RoleBinding
2. **Network Policies**: Ingress/Egress rules
3. **Pod Security**: SecurityContext, PodSecurityPolicy
4. **Image Security**: Scanning, signing, admission control
5. **Monitoring**: Falco, audit logs, intrusion detection

### 実技重視の準備
- 制限時間内での作業スピード
- kubectl コマンドの高速実行
- YAML マニフェストの即座作成
- トラブルシューティング能力

### 重要なコマンド
```bash
# RBAC確認
kubectl auth can-i --list --as=system:serviceaccount:default:test

# Network Policy テスト
kubectl run test-pod --image=busybox --rm -it -- wget -qO- http://target-service

# Pod Security Context
kubectl get pod -o jsonpath='{.spec.securityContext}'

# Falco ログ確認
journalctl -fu falco
```

## 🔗 参考リソース

### 公式リソース
- [CKS試験ガイド](https://training.linuxfoundation.org/certification/certified-kubernetes-security-specialist/)
- [Kubernetes Security Documentation](https://kubernetes.io/docs/concepts/security/)
- [CIS Kubernetes Benchmark](https://www.cisecurity.org/benchmark/kubernetes)

### 学習リソース
- [Kubernetes Security Best Practices](https://kubernetes.io/docs/concepts/security/)
- [Falco Documentation](https://falco.org/docs/)
- [OPA Gatekeeper](https://open-policy-agent.github.io/gatekeeper/)

### 実践環境
- [Killer.sh CKS Simulator](https://killer.sh/cks)
- [CKS Practice Exercises](https://github.com/walidshaari/Certified-Kubernetes-Security-Specialist)

---

**重要**: CKSは実技試験です。理論知識だけでなく、実際にコマンドを実行してセキュリティを実装する能力が評価されます。制限時間内での作業効率が合格の鍵となります。