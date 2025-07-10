# Lab 5: サプライチェーンセキュリティ

## 🎯 学習目標

このラボでは、Kubernetesクラスターにおけるサプライチェーンセキュリティの包括的な実装を学習します：

- コンテナイメージセキュリティスキャン
- イメージ署名と検証
- Admission Controller によるポリシー制御
- SBOM（Software Bill of Materials）生成
- CI/CDパイプラインセキュリティ

## 📋 前提条件

- Kubernetes クラスターが稼働中
- kubectl が設定済み
- Docker または Podman がインストール済み
- [Lab 4: マイクロサービスセキュリティ](./lab04-microservice-security.md) の完了推奨

## 🏗️ アーキテクチャ概要

```
┌─────────────────────────────────────────────────────────────┐
│                サプライチェーンセキュリティ環境                  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐     │
│  │   Image     │    │ Image Sign  │    │  Policy     │     │
│  │ Scanning    │    │ & Verify    │    │ Enforcement │     │
│  │             │    │             │    │             │     │
│  └─────┬───────┘    └─────┬───────┘    └─────┬───────┘     │
│        │                  │                  │             │
│        ▼                  ▼                  ▼             │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │               Admission Controllers                     │ │
│  │      OPA Gatekeeper + Image Policy Webhook            │ │
│  └─────┬───────────────────────┬───────────────────────────┘ │
│        │                       │                             │
│        ▼                       ▼                             │
│  ┌─────────────┐         ┌─────────────┐                     │
│  │    SBOM     │         │   CI/CD     │                     │
│  │ Generation  │         │  Pipeline   │                     │
│  └─────────────┘         └─────────────┘                     │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 Step 1: コンテナイメージセキュリティスキャン

### 1.1 Trivy セキュリティスキャナーのセットアップ

```bash
# Trivy インストール
curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh | sh -s -- -b /usr/local/bin v0.45.0

# Trivy の動作確認
trivy --version

# データベース更新
trivy image --download-db-only

echo "Trivy インストール完了"

# セキュリティスキャン実行関数
cat << 'EOF' > trivy-scan.sh
#!/bin/bash

scan_image() {
    local image=$1
    local output_format=${2:-table}
    local severity=${3:-HIGH,CRITICAL}
    
    echo "=== Scanning $image ==="
    
    # 脆弱性スキャン
    trivy image --severity $severity --format $output_format $image
    
    # 機密情報スキャン
    echo ""
    echo "=== Secret Detection ==="
    trivy fs --scanners secret --format table .
    
    # 設定ミススキャン
    echo ""
    echo "=== Misconfiguration Detection ==="
    trivy image --scanners config --format table $image
}

# 使用例
scan_image "nginx:1.21" "json" "MEDIUM,HIGH,CRITICAL"
EOF

chmod +x trivy-scan.sh
```

### 1.2 CI/CDパイプライン統合スキャン

```yaml
# GitHub Actions でのセキュリティスキャン例
cat << 'EOF' > .github/workflows/security-scan.yml
name: Container Security Scan

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  security-scan:
    runs-on: ubuntu-latest
    steps:
    - name: Checkout code
      uses: actions/checkout@v3

    - name: Build Docker image
      run: |
        docker build -t ${{ github.repository }}:${{ github.sha }} .

    - name: Run Trivy vulnerability scanner
      uses: aquasecurity/trivy-action@master
      with:
        image-ref: '${{ github.repository }}:${{ github.sha }}'
        format: 'sarif'
        output: 'trivy-results.sarif'
        severity: 'CRITICAL,HIGH'
        exit-code: '1'

    - name: Upload Trivy scan results to GitHub Security tab
      uses: github/codeql-action/upload-sarif@v2
      if: always()
      with:
        sarif_file: 'trivy-results.sarif'

    - name: Run Trivy config scanner
      uses: aquasecurity/trivy-action@master
      with:
        scan-type: 'config'
        scan-ref: '.'
        format: 'sarif'
        output: 'trivy-config.sarif'
        exit-code: '1'

    - name: SBOM Generation
      run: |
        trivy image --format spdx-json --output sbom.spdx.json ${{ github.repository }}:${{ github.sha }}

    - name: Upload SBOM
      uses: actions/upload-artifact@v3
      with:
        name: sbom
        path: sbom.spdx.json
EOF
```

### 1.3 Kubernetes内での定期スキャン

```yaml
# セキュリティスキャン用CronJob
cat << 'EOF' > security-scan-cronjob.yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: image-security-scan
  namespace: security
spec:
  schedule: "0 2 * * *"  # 毎日午前2時
  jobTemplate:
    spec:
      template:
        spec:
          serviceAccountName: security-scanner
          containers:
          - name: trivy-scanner
            image: aquasec/trivy:latest
            command:
            - /bin/sh
            - -c
            - |
              # Running Containers のイメージをスキャン
              kubectl get pods --all-namespaces -o jsonpath='{range .items[*]}{.spec.containers[*].image}{"\n"}{end}' | sort | uniq | while read image; do
                echo "Scanning $image"
                trivy image --severity HIGH,CRITICAL --format json $image > /results/$(echo $image | tr '/:' '_').json
              done
              
              # レポート生成
              echo "Security scan completed at $(date)" > /results/scan-summary.txt
              find /results -name "*.json" -exec wc -l {} \; >> /results/scan-summary.txt
            volumeMounts:
            - name: scan-results
              mountPath: /results
            - name: docker-sock
              mountPath: /var/run/docker.sock
            securityContext:
              allowPrivilegeEscalation: false
              readOnlyRootFilesystem: true
              runAsNonRoot: true
              runAsUser: 1001
              capabilities:
                drop:
                - ALL
          volumes:
          - name: scan-results
            persistentVolumeClaim:
              claimName: scan-results-pvc
          - name: docker-sock
            hostPath:
              path: /var/run/docker.sock
          restartPolicy: OnFailure
---
apiVersion: v1
kind: ServiceAccount
metadata:
  name: security-scanner
  namespace: security
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: security-scanner-role
rules:
- apiGroups: [""]
  resources: ["pods"]
  verbs: ["get", "list"]
- apiGroups: ["apps"]
  resources: ["deployments", "daemonsets", "replicasets"]
  verbs: ["get", "list"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: security-scanner-binding
subjects:
- kind: ServiceAccount
  name: security-scanner
  namespace: security
roleRef:
  kind: ClusterRole
  name: security-scanner-role
  apiGroup: rbac.authorization.k8s.io
EOF

kubectl create namespace security --dry-run=client -o yaml | kubectl apply -f -
kubectl apply -f security-scan-cronjob.yaml
```

## 🔐 Step 2: イメージ署名と検証（Cosign）

### 2.1 Cosign インストールとセットアップ

```bash
# Cosign インストール
curl -O -L "https://github.com/sigstore/cosign/releases/latest/download/cosign-linux-amd64"
sudo mv cosign-linux-amd64 /usr/local/bin/cosign
sudo chmod +x /usr/local/bin/cosign

# キーペア生成
cosign generate-key-pair

# プライベートキーをKubernetes Secretとして保存
kubectl create secret generic cosign-keys \
  --from-file=cosign.key \
  --from-file=cosign.pub \
  -n security

echo "Cosign セットアップ完了"

# イメージ署名スクリプト
cat << 'EOF' > sign-image.sh
#!/bin/bash

sign_and_verify_image() {
    local image=$1
    local private_key=${2:-cosign.key}
    local public_key=${3:-cosign.pub}
    
    echo "=== Signing image: $image ==="
    
    # イメージに署名
    COSIGN_PASSWORD="" cosign sign --key $private_key $image
    
    echo "=== Verifying signature ==="
    
    # 署名検証
    cosign verify --key $public_key $image
    
    echo "=== Generating attestation ==="
    
    # SBOM attestation
    cosign attest --predicate sbom.spdx.json --key $private_key $image
    
    echo "Image signing and verification completed"
}

# 使用例
# sign_and_verify_image "myregistry/myapp:v1.0.0"
EOF

chmod +x sign-image.sh
```

### 2.2 Kubernetes での署名検証

```yaml
# Cosign による署名検証 AdmissionController
cat << 'EOF' > cosign-admission-controller.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: cosign-webhook
  namespace: security
spec:
  replicas: 2
  selector:
    matchLabels:
      app: cosign-webhook
  template:
    metadata:
      labels:
        app: cosign-webhook
    spec:
      serviceAccountName: cosign-webhook
      containers:
      - name: webhook
        image: gcr.io/projectsigstore/cosign/cosign:latest
        command:
        - /ko-app/webhook
        env:
        - name: WEBHOOK_SECRET_NAME
          value: cosign-keys
        - name: TLS_CERT_FILE
          value: /etc/certs/tls.crt
        - name: TLS_PRIVATE_KEY_FILE
          value: /etc/certs/tls.key
        ports:
        - containerPort: 8443
        securityContext:
          allowPrivilegeEscalation: false
          readOnlyRootFilesystem: true
          runAsNonRoot: true
          runAsUser: 1001
          capabilities:
            drop:
            - ALL
        volumeMounts:
        - name: certs
          mountPath: /etc/certs
          readOnly: true
        - name: cosign-keys
          mountPath: /etc/cosign-keys
          readOnly: true
      volumes:
      - name: certs
        secret:
          secretName: cosign-webhook-certs
      - name: cosign-keys
        secret:
          secretName: cosign-keys
---
apiVersion: v1
kind: Service
metadata:
  name: cosign-webhook
  namespace: security
spec:
  selector:
    app: cosign-webhook
  ports:
  - port: 443
    targetPort: 8443
    protocol: TCP
---
apiVersion: admissionregistration.k8s.io/v1
kind: ValidatingAdmissionWebhook
metadata:
  name: cosign-image-verification
webhooks:
- name: cosign.sigstore.dev
  clientConfig:
    service:
      name: cosign-webhook
      namespace: security
      path: "/validate"
  rules:
  - operations: ["CREATE", "UPDATE"]
    apiGroups: [""]
    apiVersions: ["v1"]
    resources: ["pods"]
  - operations: ["CREATE", "UPDATE"]
    apiGroups: ["apps"]
    apiVersions: ["v1"]
    resources: ["deployments", "replicasets", "daemonsets"]
  admissionReviewVersions: ["v1", "v1beta1"]
  sideEffects: None
  failurePolicy: Fail
EOF
```

## 🛡️ Step 3: OPA Gatekeeper による政策制御

### 3.1 OPA Gatekeeper インストール

```bash
# Gatekeeper インストール
kubectl apply -f https://raw.githubusercontent.com/open-policy-agent/gatekeeper/release-3.14/deploy/gatekeeper.yaml

# インストール確認
kubectl get pods -n gatekeeper-system

echo "OPA Gatekeeper インストール完了"
```

### 3.2 セキュリティポリシーの実装

```yaml
# 許可されたレジストリのみを使用するポリシー
cat << 'EOF' > allowed-registries-policy.yaml
apiVersion: templates.gatekeeper.sh/v1beta1
kind: ConstraintTemplate
metadata:
  name: allowedregistries
spec:
  crd:
    spec:
      names:
        kind: AllowedRegistries
      validation:
        openAPIV3Schema:
          type: object
          properties:
            registries:
              type: array
              items:
                type: string
  targets:
    - target: admission.k8s.gatekeeper.sh
      rego: |
        package allowedregistries
        
        violation[{"msg": msg}] {
          container := input.review.object.spec.containers[_]
          not starts_with(container.image, input.parameters.registries[_])
          msg := sprintf("Container image '%v' does not come from allowed registry", [container.image])
        }
        
        violation[{"msg": msg}] {
          container := input.review.object.spec.initContainers[_]
          not starts_with(container.image, input.parameters.registries[_])
          msg := sprintf("Init container image '%v' does not come from allowed registry", [container.image])
        }
---
apiVersion: config.gatekeeper.sh/v1alpha1
kind: AllowedRegistries
metadata:
  name: allowed-registries-constraint
spec:
  match:
    kinds:
    - apiGroups: [""]
      kinds: ["Pod"]
    - apiGroups: ["apps"]
      kinds: ["Deployment", "ReplicaSet", "DaemonSet"]
    excludedNamespaces: ["kube-system", "gatekeeper-system", "istio-system"]
  parameters:
    registries:
    - "gcr.io/my-project/"
    - "registry.secure-company.com/"
    - "docker.io/library/"
---
# 署名されたイメージのみ許可するポリシー
apiVersion: templates.gatekeeper.sh/v1beta1
kind: ConstraintTemplate
metadata:
  name: signedimages
spec:
  crd:
    spec:
      names:
        kind: SignedImages
      validation:
        openAPIV3Schema:
          type: object
          properties:
            publicKey:
              type: string
  targets:
    - target: admission.k8s.gatekeeper.sh
      rego: |
        package signedimages
        
        violation[{"msg": msg}] {
          container := input.review.object.spec.containers[_]
          # ここでCosign検証ロジックを実装
          # 実際の実装では外部検証サービスと統合
          not image_is_signed(container.image)
          msg := sprintf("Container image '%v' is not properly signed", [container.image])
        }
        
        image_is_signed(image) {
          # 署名検証ロジック（簡略化）
          contains(image, "@sha256:")
        }
---
apiVersion: config.gatekeeper.sh/v1alpha1
kind: SignedImages
metadata:
  name: require-signed-images
spec:
  match:
    kinds:
    - apiGroups: [""]
      kinds: ["Pod"]
    - apiGroups: ["apps"]
      kinds: ["Deployment"]
    excludedNamespaces: ["kube-system", "gatekeeper-system"]
  parameters:
    publicKey: "-----BEGIN PUBLIC KEY-----\n...\n-----END PUBLIC KEY-----"
---
# 脆弱性スキャン済みイメージのみ許可
apiVersion: templates.gatekeeper.sh/v1beta1
kind: ConstraintTemplate
metadata:
  name: scannedimages
spec:
  crd:
    spec:
      names:
        kind: ScannedImages
      validation:
        openAPIV3Schema:
          type: object
          properties:
            maxSeverity:
              type: string
              enum: ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
  targets:
    - target: admission.k8s.gatekeeper.sh
      rego: |
        package scannedimages
        
        violation[{"msg": msg}] {
          container := input.review.object.spec.containers[_]
          not has_scan_annotation(input.review.object)
          msg := sprintf("Container image '%v' must have security scan annotation", [container.image])
        }
        
        violation[{"msg": msg}] {
          container := input.review.object.spec.containers[_]
          scan_severity := input.review.object.metadata.annotations["security.scan/severity"]
          scan_severity == "CRITICAL"
          msg := sprintf("Container image '%v' has CRITICAL vulnerabilities", [container.image])
        }
        
        has_scan_annotation(obj) {
          obj.metadata.annotations["security.scan/status"] == "passed"
        }
---
apiVersion: config.gatekeeper.sh/v1alpha1
kind: ScannedImages
metadata:
  name: require-scanned-images
spec:
  match:
    kinds:
    - apiGroups: [""]
      kinds: ["Pod"]
    - apiGroups: ["apps"]
      kinds: ["Deployment"]
    namespaceSelector:
      matchLabels:
        security-scan: "required"
  parameters:
    maxSeverity: "HIGH"
EOF

kubectl apply -f allowed-registries-policy.yaml
```

### 3.3 Supply Chain 監査ログ

```yaml
# Supply Chain 監査ログ設定
cat << 'EOF' > supply-chain-audit.yaml
apiVersion: audit.k8s.io/v1
kind: Policy
rules:
# イメージプル監査
- level: Metadata
  namespaces: ["production", "staging"]
  resources:
  - group: ""
    resources: ["pods"]
  verbs: ["create", "update"]
  omitStages:
  - RequestReceived
# Admission Controller 決定の監査
- level: Request
  namespaces: ["production", "staging"]
  resources:
  - group: "admissionregistration.k8s.io"
    resources: ["validatingadmissionwebhooks", "mutatingadmissionwebhooks"]
  verbs: ["create", "update", "delete"]
# Secret アクセス監査
- level: Metadata
  resources:
  - group: ""
    resources: ["secrets"]
  verbs: ["get", "list", "watch"]
  namespaces: ["security", "production"]
EOF

# 監査ログ分析スクリプト
cat << 'EOF' > analyze-supply-chain-audit.sh
#!/bin/bash

echo "=== Supply Chain Audit Analysis ==="
echo "Analysis Date: $(date)"
echo ""

# 監査ログの場所（環境に応じて調整）
AUDIT_LOG="/var/log/audit/audit.log"

if [ ! -f "$AUDIT_LOG" ]; then
    echo "Audit log not found at $AUDIT_LOG"
    echo "Please check the audit log configuration"
    exit 1
fi

echo "1. Image Pull Events Analysis:"
echo "  Recent image pulls:"
grep '"verb":"create"' $AUDIT_LOG | grep '"resource":"pods"' | \
  jq -r '.requestObject.spec.containers[].image' 2>/dev/null | \
  sort | uniq -c | sort -nr | head -10 | \
  awk '{print "    " $2 " (" $1 " times)"}'

echo ""
echo "2. Admission Controller Actions:"
echo "  Recent webhook decisions:"
grep 'ValidatingAdmissionWebhook\|MutatingAdmissionWebhook' $AUDIT_LOG | \
  jq -r '"\(.verb) \(.objectRef.name) - \(.responseStatus.code // "N/A")"' 2>/dev/null | \
  tail -5 | awk '{print "    " $0}'

echo ""
echo "3. Security Policy Violations:"
echo "  OPA Gatekeeper violations:"
grep '"reason":"ConstraintViolation"' $AUDIT_LOG | \
  jq -r '.responseStatus.message' 2>/dev/null | \
  tail -5 | awk '{print "    " $0}'

echo ""
echo "4. Suspicious Activities:"
echo "  Unusual registry usage:"
grep '"verb":"create"' $AUDIT_LOG | grep '"resource":"pods"' | \
  jq -r '.requestObject.spec.containers[].image' 2>/dev/null | \
  grep -v -E "(gcr.io|registry.secure-company.com|docker.io/library)" | \
  sort | uniq | awk '{print "    ALERT: " $0}'

echo ""
echo "=== Analysis Complete ==="
EOF

chmod +x analyze-supply-chain-audit.sh
```

## 📊 Step 4: SBOM（Software Bill of Materials）生成

### 4.1 SBOM 生成とストレージ

```bash
# Syft SBOM生成ツールのインストール
curl -sSfL https://raw.githubusercontent.com/anchore/syft/main/install.sh | sh -s -- -b /usr/local/bin

# SBOM生成スクリプト
cat << 'EOF' > generate-sbom.sh
#!/bin/bash

generate_sbom() {
    local image=$1
    local format=${2:-spdx-json}
    local output_dir=${3:-./sbom-output}
    
    mkdir -p $output_dir
    
    echo "=== Generating SBOM for $image ==="
    
    # SBOM生成
    syft $image -o $format > $output_dir/$(echo $image | tr '/:' '_').sbom.$format
    
    # 軽量版SBOM（主要コンポーネントのみ）
    syft $image -o table > $output_dir/$(echo $image | tr '/:' '_').summary.txt
    
    # 脆弱性情報付きSBOM
    grype $image -o json > $output_dir/$(echo $image | tr '/:' '_').vulnerabilities.json
    
    echo "SBOM files generated in $output_dir"
}

# Kubernetesクラスター内の全イメージのSBOM生成
generate_cluster_sbom() {
    local output_dir=${1:-./cluster-sbom}
    
    echo "=== Generating SBOM for all cluster images ==="
    
    kubectl get pods --all-namespaces -o jsonpath='{range .items[*]}{.spec.containers[*].image}{"\n"}{end}' | \
    sort | uniq | while read image; do
        echo "Processing $image"
        generate_sbom "$image" "spdx-json" "$output_dir"
    done
    
    # クラスター全体のSBOM統合レポート生成
    echo "=== Generating cluster-wide SBOM report ==="
    cat > $output_dir/cluster-sbom-report.md << EOL
# Cluster SBOM Report

Generated: $(date)

## Images Analyzed
$(ls $output_dir/*.sbom.spdx-json | wc -l) images scanned

## Summary
$(find $output_dir -name "*.summary.txt" -exec cat {} \; | grep -E "^[A-Za-z]" | sort | uniq -c | sort -nr | head -20)

## High-Risk Components
$(find $output_dir -name "*.vulnerabilities.json" -exec jq -r '.matches[] | select(.vulnerability.severity == "Critical" or .vulnerability.severity == "High") | .artifact.name' {} \; | sort | uniq -c | sort -nr | head -10)
EOL
    
    echo "Cluster SBOM report generated: $output_dir/cluster-sbom-report.md"
}

# 使用例
# generate_sbom "nginx:1.21"
# generate_cluster_sbom
EOF

chmod +x generate-sbom.sh
```

### 4.2 SBOM ストレージとバージョン管理

```yaml
# SBOM ストレージ用 StatefulSet
cat << 'EOF' > sbom-storage.yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: sbom-storage
  namespace: security
spec:
  serviceName: sbom-storage
  replicas: 1
  selector:
    matchLabels:
      app: sbom-storage
  template:
    metadata:
      labels:
        app: sbom-storage
    spec:
      containers:
      - name: storage
        image: nginx:1.21-alpine
        ports:
        - containerPort: 80
        volumeMounts:
        - name: sbom-data
          mountPath: /usr/share/nginx/html
        - name: nginx-config
          mountPath: /etc/nginx/conf.d
        securityContext:
          allowPrivilegeEscalation: false
          readOnlyRootFilesystem: true
          runAsNonRoot: true
          runAsUser: 1001
          capabilities:
            drop:
            - ALL
      volumes:
      - name: nginx-config
        configMap:
          name: sbom-nginx-config
  volumeClaimTemplates:
  - metadata:
      name: sbom-data
    spec:
      accessModes: ["ReadWriteOnce"]
      resources:
        requests:
          storage: 10Gi
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: sbom-nginx-config
  namespace: security
data:
  default.conf: |
    server {
        listen 80;
        server_name localhost;
        
        location / {
            root /usr/share/nginx/html;
            index index.html;
            autoindex on;
            autoindex_exact_size off;
        }
        
        location ~ \.json$ {
            add_header Content-Type application/json;
        }
        
        location /api/sbom {
            alias /usr/share/nginx/html;
            try_files $uri $uri/ =404;
        }
    }
---
apiVersion: v1
kind: Service
metadata:
  name: sbom-storage
  namespace: security
spec:
  selector:
    app: sbom-storage
  ports:
  - port: 80
    targetPort: 80
  type: ClusterIP
EOF

kubectl apply -f sbom-storage.yaml
```

## 🔄 Step 5: CI/CD パイプラインセキュリティ

### 5.1 セキュアCI/CDパイプライン設定

```yaml
# GitLab CI でのセキュアパイプライン例
cat << 'EOF' > .gitlab-ci.yml
stages:
  - security-scan
  - build
  - test
  - sign
  - deploy

variables:
  DOCKER_DRIVER: overlay2
  DOCKER_TLS_CERTDIR: ""
  REGISTRY: $CI_REGISTRY
  IMAGE_TAG: $CI_COMMIT_SHA

# セキュリティスキャンステージ
security-scan:
  stage: security-scan
  image: aquasec/trivy:latest
  services:
    - docker:20.10-dind
  script:
    # ソースコード脆弱性スキャン
    - trivy fs --severity HIGH,CRITICAL --format sarif --output trivy-code-scan.sarif .
    # 機密情報スキャン
    - trivy fs --scanners secret --format json --output secret-scan.json .
    # Infrastructure as Code スキャン
    - trivy fs --scanners config --format json --output iac-scan.json .
  artifacts:
    reports:
      sast: trivy-code-scan.sarif
    paths:
      - "*.json"
    expire_in: 1 week
  allow_failure: false

# イメージビルド
build:
  stage: build
  image: docker:20.10
  services:
    - docker:20.10-dind
  script:
    - docker build -t $REGISTRY/$CI_PROJECT_PATH:$IMAGE_TAG .
    - docker push $REGISTRY/$CI_PROJECT_PATH:$IMAGE_TAG
  dependencies:
    - security-scan

# イメージセキュリティテスト
image-security-test:
  stage: test
  image: aquasec/trivy:latest
  script:
    # イメージ脆弱性スキャン
    - trivy image --severity HIGH,CRITICAL --format sarif --output image-scan.sarif $REGISTRY/$CI_PROJECT_PATH:$IMAGE_TAG
    # SBOM生成
    - trivy image --format spdx-json --output sbom.spdx.json $REGISTRY/$CI_PROJECT_PATH:$IMAGE_TAG
  artifacts:
    reports:
      container_scanning: image-scan.sarif
    paths:
      - sbom.spdx.json
    expire_in: 1 week
  dependencies:
    - build

# イメージ署名
sign-image:
  stage: sign
  image: gcr.io/projectsigstore/cosign:latest
  script:
    # Cosignでイメージに署名
    - echo $COSIGN_PRIVATE_KEY | base64 -d > cosign.key
    - COSIGN_PASSWORD=$COSIGN_PASSWORD cosign sign --key cosign.key $REGISTRY/$CI_PROJECT_PATH:$IMAGE_TAG
    # SBOM Attestation
    - cosign attest --predicate sbom.spdx.json --key cosign.key $REGISTRY/$CI_PROJECT_PATH:$IMAGE_TAG
  dependencies:
    - image-security-test
  only:
    - main
    - develop

# セキュア デプロイメント
deploy:
  stage: deploy
  image: bitnami/kubectl:latest
  script:
    # デプロイメント前の署名検証
    - cosign verify --key cosign.pub $REGISTRY/$CI_PROJECT_PATH:$IMAGE_TAG
    # Kubernetesへデプロイ
    - kubectl set image deployment/myapp myapp=$REGISTRY/$CI_PROJECT_PATH:$IMAGE_TAG
    - kubectl rollout status deployment/myapp
  environment:
    name: production
  dependencies:
    - sign-image
  only:
    - main
EOF
```

### 5.2 Pipeline セキュリティ監視

```bash
# CI/CD セキュリティ監視スクリプト
cat << 'EOF' > monitor-pipeline-security.sh
#!/bin/bash

echo "=== CI/CD Pipeline Security Monitoring ==="
echo "Monitor Date: $(date)"
echo ""

# 1. 最近の脆弱性スキャン結果確認
echo "1. Recent Vulnerability Scan Results:"
if [ -d "scan-results" ]; then
    find scan-results -name "*.json" -mtime -7 | while read file; do
        echo "  File: $file"
        if command -v jq >/dev/null; then
            high_count=$(jq '[.Results[]?.Vulnerabilities[]? | select(.Severity == "HIGH")] | length' "$file" 2>/dev/null || echo "0")
            critical_count=$(jq '[.Results[]?.Vulnerabilities[]? | select(.Severity == "CRITICAL")] | length' "$file" 2>/dev/null || echo "0")
            echo "    HIGH: $high_count, CRITICAL: $critical_count"
        fi
    done
else
    echo "  No scan results directory found"
fi

echo ""

# 2. 署名検証ログ
echo "2. Image Signature Verification:"
if [ -f "cosign-verification.log" ]; then
    tail -5 cosign-verification.log | awk '{print "  " $0}'
else
    echo "  No signature verification log found"
fi

echo ""

# 3. 失敗したセキュリティゲート
echo "3. Failed Security Gates (Last 24h):"
if [ -f "pipeline.log" ]; then
    grep -i "security.*fail\|vulnerability.*fail\|signature.*fail" pipeline.log | tail -5 | awk '{print "  " $0}'
else
    echo "  No pipeline log found"
fi

echo ""

# 4. 依存関係の変更監視
echo "4. Dependency Changes:"
if [ -f "sbom-current.json" ] && [ -f "sbom-previous.json" ]; then
    echo "  Comparing current SBOM with previous version..."
    # SBOM差分分析（簡略版）
    current_pkgs=$(jq -r '.packages[].name' sbom-current.json 2>/dev/null | sort)
    previous_pkgs=$(jq -r '.packages[].name' sbom-previous.json 2>/dev/null | sort)
    
    new_packages=$(comm -13 <(echo "$previous_pkgs") <(echo "$current_pkgs"))
    removed_packages=$(comm -23 <(echo "$previous_pkgs") <(echo "$current_pkgs"))
    
    if [ -n "$new_packages" ]; then
        echo "  New packages added:"
        echo "$new_packages" | head -5 | awk '{print "    + " $0}'
    fi
    
    if [ -n "$removed_packages" ]; then
        echo "  Packages removed:"
        echo "$removed_packages" | head -5 | awk '{print "    - " $0}'
    fi
else
    echo "  SBOM files not found for comparison"
fi

echo ""

# 5. セキュリティメトリクス
echo "5. Security Metrics Summary:"
if [ -d "metrics" ]; then
    echo "  Scan frequency: $(find metrics -name "scan-*.json" -mtime -7 | wc -l) scans in last 7 days"
    echo "  Signature rate: $(find metrics -name "sign-*.log" -mtime -7 | wc -l) images signed in last 7 days"
    
    # 平均修復時間計算（例）
    if [ -f "metrics/fix-times.log" ]; then
        avg_fix_time=$(awk '{sum+=$1; count++} END {print sum/count}' metrics/fix-times.log 2>/dev/null || echo "N/A")
        echo "  Avg vulnerability fix time: $avg_fix_time hours"
    fi
fi

echo ""
echo "=== Security Monitoring Complete ==="

# アラート条件チェック
echo ""
echo "=== Security Alerts ==="

# Critical 脆弱性チェック
if [ -f "scan-results/latest.json" ]; then
    critical_vulns=$(jq '[.Results[]?.Vulnerabilities[]? | select(.Severity == "CRITICAL")] | length' scan-results/latest.json 2>/dev/null || echo "0")
    if [ "$critical_vulns" -gt 0 ]; then
        echo "🚨 ALERT: $critical_vulns CRITICAL vulnerabilities found!"
    fi
fi

# 署名失敗チェック
if grep -q "signature verification failed" cosign-verification.log 2>/dev/null; then
    echo "🚨 ALERT: Image signature verification failed!"
fi

# 異常な依存関係追加チェック
if [ -n "$new_packages" ] && [ $(echo "$new_packages" | wc -l) -gt 10 ]; then
    echo "⚠️ WARNING: Unusual number of new dependencies added ($(echo "$new_packages" | wc -l))"
fi

echo "=== Alerts Complete ==="
EOF

chmod +x monitor-pipeline-security.sh
```

## 🧹 Step 6: クリーンアップ

```bash
# テスト用リソースの削除
kubectl delete namespace security --ignore-not-found
kubectl delete cronjob image-security-scan -n security --ignore-not-found
kubectl delete deployment cosign-webhook -n security --ignore-not-found
kubectl delete statefulset sbom-storage -n security --ignore-not-found

# OPA Gatekeeper の制約削除
kubectl delete allowedregistries allowed-registries-constraint --ignore-not-found
kubectl delete signedimages require-signed-images --ignore-not-found
kubectl delete scannedimages require-scanned-images --ignore-not-found

# OPA Gatekeeper アンインストール（必要に応じて）
# kubectl delete -f https://raw.githubusercontent.com/open-policy-agent/gatekeeper/release-3.14/deploy/gatekeeper.yaml

echo "クリーンアップ完了"
```

## 💰 コスト計算

- **Trivy スキャン**: 既存インフラ内実行のため追加コストなし
- **イメージストレージ**: 署名・SBOM用に約20%増加
- **OPA Gatekeeper**: 約100MB追加メモリ使用
- **監視・ログ**: 約500MB追加ストレージ
- **総追加コスト**: 月額約$20-50（クラスターサイズにより変動）

## 📚 学習ポイント

### 重要な概念
1. **Supply Chain Security**: ソフトウェア供給チェーン全体のセキュリティ
2. **Image Signing**: Cosignによるコンテナイメージの完全性保証
3. **Policy as Code**: OPA Gatekeeperによる宣言的セキュリティポリシー
4. **SBOM**: ソフトウェア部品表による透明性確保
5. **Shift-Left Security**: CI/CDパイプライン早期でのセキュリティチェック

### 実践的なスキル
- コンテナイメージの脆弱性スキャンと修復
- Cosignによるイメージ署名と検証の実装
- OPA Gatekeeperによるアドミッションコントロール
- SBOMの生成・管理・活用
- セキュアなCI/CDパイプラインの構築

---

**次のステップ**: [Lab 6: 監視・ランタイムセキュリティ](./lab06-monitoring-runtime-security.md) では、実行時セキュリティ監視とインシデント対応を学習します。