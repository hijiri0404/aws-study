# Lab 6: 監視・ランタイムセキュリティ

## 🎯 学習目標

このラボでは、Kubernetesクラスターにおける実行時セキュリティ監視とインシデント対応を学習します：

- 実行時脅威検知とレスポンス
- セキュリティイベント監視とアラート
- 異常行動検知（Anomaly Detection）
- インシデント対応とフォレンジック
- コンプライアンス監査とレポート

## 📋 前提条件

- Kubernetes クラスターが稼働中
- kubectl が設定済み
- Prometheus/Grafana が設定済み
- [Lab 5: サプライチェーンセキュリティ](./lab05-supply-chain-security.md) の完了推奨

## 🏗️ アーキテクチャ概要

```
┌─────────────────────────────────────────────────────────────┐
│               監視・ランタイムセキュリティ環境                   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐     │
│  │ Runtime     │    │ Anomaly     │    │ Incident    │     │
│  │ Threat      │    │ Detection   │    │ Response    │     │
│  │ Detection   │    │             │    │             │     │
│  └─────┬───────┘    └─────┬───────┘    └─────┬───────┘     │
│        │                  │                  │             │
│        ▼                  ▼                  ▼             │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │              Security Event Aggregation                │ │
│  │    Falco + SIEM + Prometheus + Jaeger + Audit         │ │
│  └─────┬───────────────────────┬───────────────────────────┘ │
│        │                       │                             │
│        ▼                       ▼                             │
│  ┌─────────────┐         ┌─────────────┐                     │
│  │ Compliance  │         │ Forensics   │                     │
│  │ Monitoring  │         │ & Analysis  │                     │
│  └─────────────┘         └─────────────┘                     │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 Step 1: Falco による実行時脅威検知

### 1.1 Falco インストールと設定

```bash
# Falco Helm チャートリポジトリ追加
helm repo add falcosecurity https://falcosecurity.github.io/charts
helm repo update

# Falco インストール
kubectl create namespace falco-system

cat << 'EOF' > falco-values.yaml
falco:
  syscall_event_drops:
    max_burst: 1000
    rate: 100
  grpc:
    enabled: true
    bind_address: "0.0.0.0:5060"
    threadiness: 8

driver:
  enabled: true
  kind: ebpf

falcoctl:
  enabled: true

serviceMonitor:
  enabled: true

grafanaDashboard:
  enabled: true

falcosidekick:
  enabled: true
  webui:
    enabled: true
    service:
      type: ClusterIP
  config:
    webhook:
      address: "http://security-webhook.security.svc.cluster.local:8080"
    prometheus:
      address: "http://prometheus.monitoring.svc.cluster.local:9090"
    elasticsearch:
      hostport: "http://elasticsearch.security.svc.cluster.local:9200"
EOF

helm install falco falcosecurity/falco \
  --namespace falco-system \
  --values falco-values.yaml

echo "Falco インストール完了"
```

### 1.2 カスタム Falco ルール

```yaml
# カスタムセキュリティルール
cat << 'EOF' > custom-falco-rules.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: falco-custom-rules
  namespace: falco-system
  labels:
    app: falco
data:
  custom_rules.yaml: |
    # Kubernetes セキュリティルール
    
    # 1. 権限昇格の検知
    - rule: Detect Privilege Escalation
      desc: Detect attempts to escalate privileges
      condition: >
        spawned_process and
        (proc.name in (sudo, su, doas) or
         proc.args contains setuid or
         proc.args contains setgid)
      output: >
        Privilege escalation attempt detected
        (user=%user.name command=%proc.cmdline pid=%proc.pid container=%container.name image=%container.image)
      priority: WARNING
      tags: [privilege_escalation, security]
    
    # 2. 機密ファイルアクセス
    - rule: Read Sensitive Files
      desc: Detect reading of sensitive files
      condition: >
        open_read and
        (fd.name in (/etc/shadow, /etc/passwd, /etc/sudoers, /root/.ssh/id_rsa) or
         fd.name startswith /proc/self/mem or
         fd.name startswith /dev/mem)
      output: >
        Sensitive file accessed
        (user=%user.name command=%proc.cmdline file=%fd.name container=%container.name)
      priority: WARNING
      tags: [sensitive_files, security]
    
    # 3. ネットワーク接続の監視
    - rule: Outbound Connection to Suspicious Domains
      desc: Detect outbound connections to suspicious domains
      condition: >
        outbound and
        (fd.sip.name contains .onion or
         fd.sip.name contains pastebin.com or
         fd.sip.name contains paste.org or
         fd.sip.name endswith .tk or
         fd.sip.name endswith .ml)
      output: >
        Suspicious outbound connection
        (user=%user.name command=%proc.cmdline connection=%fd.name container=%container.name)
      priority: WARNING
      tags: [network, suspicious]
    
    # 4. コンテナエスケープの検知
    - rule: Container Escape Attempt
      desc: Detect attempts to escape container
      condition: >
        spawned_process and
        (proc.name in (mount, umount, chroot, pivot_root) or
         proc.args contains /proc/self/ns or
         proc.args contains /proc/self/root or
         proc.args contains --privileged)
      output: >
        Container escape attempt detected
        (user=%user.name command=%proc.cmdline container=%container.name image=%container.image)
      priority: CRITICAL
      tags: [container_escape, security]
    
    # 5. 異常なシステムコール
    - rule: Unusual System Activity
      desc: Detect unusual system activities
      condition: >
        syscall and
        (evt.type in (ptrace, process_vm_readv, process_vm_writev) or
         evt.type contains unshare or
         evt.type contains clone and proc.args contains CLONE_NEWNS)
      output: >
        Unusual system activity detected
        (user=%user.name command=%proc.cmdline syscall=%evt.type container=%container.name)
      priority: INFO
      tags: [system_activity, monitoring]
    
    # 6. Kubernetes API 異常アクセス
    - rule: Kubernetes API Abuse
      desc: Detect suspicious Kubernetes API access
      condition: >
        ka_verb and
        (ka_verb in (create, update, patch, delete) and
         ka_resource_name contains secret and
         not ka_user_name startswith system:) or
        (ka_verb=delete and ka_resource_name contains namespace)
      output: >
        Suspicious Kubernetes API access
        (user=%ka_user_name verb=%ka_verb resource=%ka_target_resource)
      priority: WARNING
      tags: [k8s_api, security]
    
    # 7. コンテナ内でのパッケージ管理
    - rule: Package Management in Container
      desc: Detect package installation in running containers
      condition: >
        spawned_process and container and
        (proc.name in (apt, apt-get, yum, dnf, pip, npm, gem, cargo) and
         proc.args contains install)
      output: >
        Package installation in running container
        (user=%user.name command=%proc.cmdline container=%container.name image=%container.image)
      priority: INFO
      tags: [package_management, container]
    
    # 8. ファイルシステム改ざん
    - rule: File System Tampering
      desc: Detect file system tampering
      condition: >
        (open_write or rename or unlink) and
        (fd.name startswith /etc/ or
         fd.name startswith /usr/bin/ or
         fd.name startswith /usr/sbin/ or
         fd.name startswith /bin/ or
         fd.name startswith /sbin/) and
        not proc.name in (apt, apt-get, yum, dnf, rpm, dpkg)
      output: >
        File system tampering detected
        (user=%user.name command=%proc.cmdline file=%fd.name container=%container.name)
      priority: WARNING
      tags: [file_tampering, security]
    
    # 9. 暗号化マイニング検知
    - rule: Crypto Mining Activity
      desc: Detect potential crypto mining activities
      condition: >
        spawned_process and
        (proc.name in (xmrig, minerd, cpuminer, cgminer, bfgminer) or
         proc.args contains stratum+ or
         proc.args contains mining.pool or
         proc.cmdline contains --donate-level)
      output: >
        Potential crypto mining activity detected
        (user=%user.name command=%proc.cmdline container=%container.name)
      priority: CRITICAL
      tags: [crypto_mining, security]
    
    # 10. データ流出の検知
    - rule: Data Exfiltration Attempt
      desc: Detect potential data exfiltration
      condition: >
        outbound and
        (fd.directory contains /var/log or
         fd.directory contains /etc or
         fd.directory contains /root) and
        fd.sip != "127.0.0.1" and
        not fd.sip in (kubernetes_service_ips)
      output: >
        Potential data exfiltration detected
        (user=%user.name command=%proc.cmdline file=%fd.name connection=%fd.sip container=%container.name)
      priority: CRITICAL
      tags: [data_exfiltration, security]
EOF

kubectl apply -f custom-falco-rules.yaml

# Falco 再起動でルール適用
kubectl rollout restart daemonset/falco -n falco-system
```

### 1.3 セキュリティアラート Webhook

```yaml
# セキュリティアラート処理用 Webhook
cat << 'EOF' > security-webhook.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: security-webhook
  namespace: security
spec:
  replicas: 2
  selector:
    matchLabels:
      app: security-webhook
  template:
    metadata:
      labels:
        app: security-webhook
    spec:
      containers:
      - name: webhook
        image: python:3.9-alpine
        ports:
        - containerPort: 8080
        env:
        - name: SLACK_WEBHOOK_URL
          valueFrom:
            secretKeyRef:
              name: alert-secrets
              key: slack-webhook-url
        - name: EMAIL_SMTP_SERVER
          value: "smtp.company.com"
        command:
        - /bin/sh
        - -c
        - |
          cat > webhook.py << 'PYTHON_EOF'
          import json
          import requests
          import smtplib
          from datetime import datetime
          from http.server import HTTPServer, BaseHTTPRequestHandler
          from email.mime.text import MIMEText
          import os
          
          class SecurityWebhookHandler(BaseHTTPRequestHandler):
              def do_POST(self):
                  content_length = int(self.headers['Content-Length'])
                  post_data = self.rfile.read(content_length)
                  
                  try:
                      alert_data = json.loads(post_data.decode('utf-8'))
                      self.process_security_alert(alert_data)
                      
                      self.send_response(200)
                      self.send_header('Content-type', 'application/json')
                      self.end_headers()
                      self.wfile.write(json.dumps({"status": "processed"}).encode())
                      
                  except Exception as e:
                      print(f"Error processing alert: {e}")
                      self.send_response(500)
                      self.end_headers()
              
              def process_security_alert(self, alert):
                  print(f"Processing security alert: {json.dumps(alert, indent=2)}")
                  
                  # アラートの重要度判定
                  priority = alert.get('priority', 'INFO')
                  rule_name = alert.get('rule', 'Unknown')
                  
                  # 高優先度アラートの処理
                  if priority in ['CRITICAL', 'WARNING']:
                      self.send_slack_alert(alert)
                      
                      if priority == 'CRITICAL':
                          self.send_email_alert(alert)
                          self.trigger_incident_response(alert)
                  
                  # すべてのアラートをログに記録
                  self.log_security_event(alert)
              
              def send_slack_alert(self, alert):
                  slack_url = os.getenv('SLACK_WEBHOOK_URL')
                  if not slack_url:
                      return
                  
                  message = {
                      "text": f"🚨 Security Alert: {alert.get('rule', 'Unknown')}",
                      "attachments": [
                          {
                              "color": "danger" if alert.get('priority') == 'CRITICAL' else "warning",
                              "fields": [
                                  {"title": "Priority", "value": alert.get('priority', 'Unknown'), "short": True},
                                  {"title": "Container", "value": alert.get('output_fields', {}).get('container.name', 'N/A'), "short": True},
                                  {"title": "Command", "value": alert.get('output_fields', {}).get('proc.cmdline', 'N/A'), "short": False},
                                  {"title": "Time", "value": alert.get('time', 'Unknown'), "short": True}
                              ]
                          }
                      ]
                  }
                  
                  try:
                      requests.post(slack_url, json=message, timeout=10)
                  except Exception as e:
                      print(f"Failed to send Slack alert: {e}")
              
              def send_email_alert(self, alert):
                  # Critical アラートのメール通知
                  smtp_server = os.getenv('EMAIL_SMTP_SERVER')
                  if not smtp_server:
                      return
                  
                  subject = f"CRITICAL Security Alert: {alert.get('rule', 'Unknown')}"
                  body = f"""
          A critical security alert has been detected:
          
          Rule: {alert.get('rule', 'Unknown')}
          Priority: {alert.get('priority', 'Unknown')}
          Time: {alert.get('time', 'Unknown')}
          
          Details:
          {json.dumps(alert.get('output_fields', {}), indent=2)}
          
          Full Alert:
          {json.dumps(alert, indent=2)}
                  """
                  
                  try:
                      msg = MIMEText(body)
                      msg['Subject'] = subject
                      msg['From'] = 'security@company.com'
                      msg['To'] = 'security-team@company.com'
                      
                      # SMTP設定は環境に応じて調整
                      print(f"Email alert would be sent: {subject}")
                  except Exception as e:
                      print(f"Failed to send email alert: {e}")
              
              def trigger_incident_response(self, alert):
                  # インシデント対応プロセスのトリガー
                  incident_data = {
                      "alert_id": f"SEC-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
                      "severity": alert.get('priority', 'UNKNOWN'),
                      "rule": alert.get('rule', 'Unknown'),
                      "container": alert.get('output_fields', {}).get('container.name'),
                      "image": alert.get('output_fields', {}).get('container.image'),
                      "user": alert.get('output_fields', {}).get('user.name'),
                      "command": alert.get('output_fields', {}).get('proc.cmdline'),
                      "timestamp": alert.get('time')
                  }
                  
                  print(f"Triggering incident response for: {incident_data['alert_id']}")
                  
                  # ここで実際のインシデント対応システムとの連携を実装
                  # 例: ServiceNow, PagerDuty, JIRA等との連携
              
              def log_security_event(self, alert):
                  # セキュリティイベントの構造化ログ出力
                  log_entry = {
                      "timestamp": datetime.now().isoformat(),
                      "event_type": "security_alert",
                      "source": "falco",
                      "alert_data": alert
                  }
                  
                  print(f"SECURITY_EVENT: {json.dumps(log_entry)}")
          
          if __name__ == "__main__":
              server = HTTPServer(('0.0.0.0', 8080), SecurityWebhookHandler)
              print("Security webhook server starting on port 8080...")
              server.serve_forever()
          PYTHON_EOF
          
          pip install requests
          python webhook.py
        securityContext:
          allowPrivilegeEscalation: false
          readOnlyRootFilesystem: true
          runAsNonRoot: true
          runAsUser: 1001
          capabilities:
            drop:
            - ALL
        volumeMounts:
        - name: tmp-volume
          mountPath: /tmp
      volumes:
      - name: tmp-volume
        emptyDir: {}
---
apiVersion: v1
kind: Service
metadata:
  name: security-webhook
  namespace: security
spec:
  selector:
    app: security-webhook
  ports:
  - port: 8080
    targetPort: 8080
  type: ClusterIP
---
apiVersion: v1
kind: Secret
metadata:
  name: alert-secrets
  namespace: security
type: Opaque
data:
  slack-webhook-url: aHR0cHM6Ly9ob29rcy5zbGFjay5jb20vc2VydmljZXMvWE9VUi9TTEFTL1dFQkhPT0svVVJM  # Your Slack webhook URL
EOF

kubectl apply -f security-webhook.yaml
```

## 📊 Step 2: 異常行動検知システム

### 2.1 機械学習ベース異常検知

```python
# 異常検知アルゴリズム実装
cat << 'EOF' > anomaly-detection.py
#!/usr/bin/env python3

import numpy as np
import pandas as pd
import json
import requests
from datetime import datetime, timedelta
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import DBSCAN
import joblib
import time

class KubernetesAnomalyDetector:
    def __init__(self):
        self.isolation_forest = IsolationForest(contamination=0.1, random_state=42)
        self.scaler = StandardScaler()
        self.dbscan = DBSCAN(eps=0.5, min_samples=5)
        self.baseline_data = None
        
    def collect_metrics(self, prometheus_url="http://prometheus.monitoring.svc.cluster.local:9090"):
        """Prometheusからメトリクスを収集"""
        queries = {
            'cpu_usage': 'rate(container_cpu_usage_seconds_total[5m])',
            'memory_usage': 'container_memory_usage_bytes',
            'network_rx': 'rate(container_network_receive_bytes_total[5m])',
            'network_tx': 'rate(container_network_transmit_bytes_total[5m])',
            'file_descriptor_usage': 'container_file_descriptors',
            'process_count': 'container_processes',
            'syscalls_per_second': 'rate(container_syscalls_total[5m])'
        }
        
        metrics_data = {}
        
        for metric_name, query in queries.items():
            try:
                response = requests.get(
                    f"{prometheus_url}/api/v1/query",
                    params={'query': query},
                    timeout=30
                )
                
                if response.status_code == 200:
                    data = response.json()
                    metrics_data[metric_name] = self.parse_prometheus_response(data)
                else:
                    print(f"Failed to query {metric_name}: {response.status_code}")
                    
            except Exception as e:
                print(f"Error querying {metric_name}: {e}")
                
        return metrics_data
    
    def parse_prometheus_response(self, response_data):
        """Prometheusレスポンスをパース"""
        result = []
        
        if 'data' in response_data and 'result' in response_data['data']:
            for item in response_data['data']['result']:
                metric_info = {
                    'labels': item.get('metric', {}),
                    'value': float(item['value'][1]) if item.get('value') else 0,
                    'timestamp': item['value'][0] if item.get('value') else 0
                }
                result.append(metric_info)
                
        return result
    
    def prepare_features(self, metrics_data):
        """特徴量エンジニアリング"""
        features = []
        
        for container_metrics in self.aggregate_by_container(metrics_data):
            feature_vector = [
                container_metrics.get('cpu_usage', 0),
                container_metrics.get('memory_usage', 0),
                container_metrics.get('network_rx', 0),
                container_metrics.get('network_tx', 0),
                container_metrics.get('file_descriptor_usage', 0),
                container_metrics.get('process_count', 0),
                container_metrics.get('syscalls_per_second', 0),
                # 計算された特徴量
                container_metrics.get('network_rx', 0) + container_metrics.get('network_tx', 0),  # total_network
                container_metrics.get('cpu_usage', 0) / max(container_metrics.get('memory_usage', 1), 1),  # cpu_memory_ratio
                container_metrics.get('syscalls_per_second', 0) / max(container_metrics.get('process_count', 1), 1)  # syscalls_per_process
            ]
            
            features.append({
                'container_name': container_metrics.get('container_name', 'unknown'),
                'namespace': container_metrics.get('namespace', 'unknown'),
                'pod_name': container_metrics.get('pod_name', 'unknown'),
                'features': feature_vector
            })
            
        return features
    
    def aggregate_by_container(self, metrics_data):
        """コンテナごとにメトリクスを集約"""
        container_map = {}
        
        for metric_name, metric_list in metrics_data.items():
            for metric in metric_list:
                labels = metric['labels']
                container_key = f"{labels.get('namespace', 'unknown')}/{labels.get('pod', 'unknown')}/{labels.get('container', 'unknown')}"
                
                if container_key not in container_map:
                    container_map[container_key] = {
                        'container_name': labels.get('container', 'unknown'),
                        'namespace': labels.get('namespace', 'unknown'),
                        'pod_name': labels.get('pod', 'unknown')
                    }
                
                container_map[container_key][metric_name] = metric['value']
        
        return list(container_map.values())
    
    def train_baseline(self, training_data):
        """ベースライン学習"""
        feature_vectors = [item['features'] for item in training_data]
        
        if len(feature_vectors) < 10:
            print("Insufficient training data")
            return False
            
        # 特徴量の正規化
        scaled_features = self.scaler.fit_transform(feature_vectors)
        
        # Isolation Forestの学習
        self.isolation_forest.fit(scaled_features)
        
        # クラスタリングベースライン
        self.dbscan.fit(scaled_features)
        
        self.baseline_data = {
            'feature_means': np.mean(scaled_features, axis=0),
            'feature_stds': np.std(scaled_features, axis=0),
            'timestamp': datetime.now().isoformat()
        }
        
        print(f"Baseline trained with {len(feature_vectors)} samples")
        return True
    
    def detect_anomalies(self, current_data):
        """異常検知実行"""
        if not self.baseline_data:
            print("No baseline available for anomaly detection")
            return []
            
        anomalies = []
        feature_vectors = [item['features'] for item in current_data]
        
        if not feature_vectors:
            return anomalies
            
        # 特徴量の正規化
        scaled_features = self.scaler.transform(feature_vectors)
        
        # Isolation Forest による異常検知
        anomaly_scores = self.isolation_forest.decision_function(scaled_features)
        anomaly_predictions = self.isolation_forest.predict(scaled_features)
        
        for i, prediction in enumerate(anomaly_predictions):
            if prediction == -1:  # 異常
                anomaly_info = {
                    'container_name': current_data[i]['container_name'],
                    'namespace': current_data[i]['namespace'],
                    'pod_name': current_data[i]['pod_name'],
                    'anomaly_score': float(anomaly_scores[i]),
                    'anomaly_type': 'isolation_forest',
                    'features': current_data[i]['features'],
                    'timestamp': datetime.now().isoformat(),
                    'severity': self.calculate_severity(anomaly_scores[i])
                }
                anomalies.append(anomaly_info)
        
        # 統計的異常検知
        statistical_anomalies = self.detect_statistical_anomalies(scaled_features, current_data)
        anomalies.extend(statistical_anomalies)
        
        return anomalies
    
    def detect_statistical_anomalies(self, scaled_features, current_data):
        """統計的異常検知"""
        anomalies = []
        baseline_means = self.baseline_data['feature_means']
        baseline_stds = self.baseline_data['feature_stds']
        
        for i, features in enumerate(scaled_features):
            # Z-score ベース異常検知
            z_scores = np.abs((features - baseline_means) / (baseline_stds + 1e-8))
            max_z_score = np.max(z_scores)
            
            if max_z_score > 3:  # 3-sigma rule
                anomaly_info = {
                    'container_name': current_data[i]['container_name'],
                    'namespace': current_data[i]['namespace'],
                    'pod_name': current_data[i]['pod_name'],
                    'anomaly_score': float(max_z_score),
                    'anomaly_type': 'statistical',
                    'features': current_data[i]['features'],
                    'timestamp': datetime.now().isoformat(),
                    'severity': self.calculate_severity(-max_z_score)  # 負の値で統一
                }
                anomalies.append(anomaly_info)
        
        return anomalies
    
    def calculate_severity(self, anomaly_score):
        """異常度から重要度を計算"""
        if anomaly_score < -0.6:
            return 'CRITICAL'
        elif anomaly_score < -0.4:
            return 'HIGH'
        elif anomaly_score < -0.2:
            return 'MEDIUM'
        else:
            return 'LOW'
    
    def send_anomaly_alert(self, anomaly):
        """異常アラートの送信"""
        alert_data = {
            'rule': f"Anomaly Detected: {anomaly['anomaly_type']}",
            'priority': anomaly['severity'],
            'time': anomaly['timestamp'],
            'output_fields': {
                'container.name': anomaly['container_name'],
                'namespace': anomaly['namespace'],
                'pod.name': anomaly['pod_name'],
                'anomaly.score': anomaly['anomaly_score'],
                'anomaly.type': anomaly['anomaly_type']
            }
        }
        
        try:
            response = requests.post(
                'http://security-webhook.security.svc.cluster.local:8080',
                json=alert_data,
                timeout=10
            )
            
            if response.status_code == 200:
                print(f"Anomaly alert sent for {anomaly['container_name']}")
            else:
                print(f"Failed to send anomaly alert: {response.status_code}")
                
        except Exception as e:
            print(f"Error sending anomaly alert: {e}")
    
    def save_model(self, filepath):
        """モデルの保存"""
        model_data = {
            'isolation_forest': self.isolation_forest,
            'scaler': self.scaler,
            'baseline_data': self.baseline_data
        }
        joblib.dump(model_data, filepath)
        
    def load_model(self, filepath):
        """モデルの読み込み"""
        try:
            model_data = joblib.load(filepath)
            self.isolation_forest = model_data['isolation_forest']
            self.scaler = model_data['scaler'] 
            self.baseline_data = model_data['baseline_data']
            return True
        except Exception as e:
            print(f"Failed to load model: {e}")
            return False

def main():
    detector = KubernetesAnomalyDetector()
    
    # モデルの読み込み試行
    if not detector.load_model('/models/anomaly_model.pkl'):
        print("No existing model found, starting baseline training...")
        
        # ベースライン学習用データ収集（1時間）
        training_data = []
        for _ in range(12):  # 5分間隔で12回
            metrics = detector.collect_metrics()
            features = detector.prepare_features(metrics)
            training_data.extend(features)
            time.sleep(300)  # 5分待機
            
        if detector.train_baseline(training_data):
            detector.save_model('/models/anomaly_model.pkl')
    
    print("Starting real-time anomaly detection...")
    
    # リアルタイム異常検知
    while True:
        try:
            # メトリクス収集
            metrics = detector.collect_metrics()
            features = detector.prepare_features(metrics)
            
            # 異常検知実行
            anomalies = detector.detect_anomalies(features)
            
            # 異常があればアラート送信
            for anomaly in anomalies:
                print(f"Anomaly detected: {json.dumps(anomaly, indent=2)}")
                detector.send_anomaly_alert(anomaly)
            
            if not anomalies:
                print(f"No anomalies detected at {datetime.now().isoformat()}")
            
            time.sleep(60)  # 1分間隔
            
        except KeyboardInterrupt:
            print("Stopping anomaly detection...")
            break
        except Exception as e:
            print(f"Error in anomaly detection loop: {e}")
            time.sleep(60)

if __name__ == "__main__":
    main()
EOF

chmod +x anomaly-detection.py
```

### 2.2 異常検知 Deployment

```yaml
# 異常検知システムのデプロイ
cat << 'EOF' > anomaly-detection-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: anomaly-detector
  namespace: security
spec:
  replicas: 1
  selector:
    matchLabels:
      app: anomaly-detector
  template:
    metadata:
      labels:
        app: anomaly-detector
    spec:
      containers:
      - name: detector
        image: python:3.9-slim
        command:
        - /bin/bash
        - -c
        - |
          pip install numpy pandas scikit-learn requests joblib
          cd /app
          python anomaly-detection.py
        volumeMounts:
        - name: detector-code
          mountPath: /app
        - name: model-storage
          mountPath: /models
        securityContext:
          allowPrivilegeEscalation: false
          readOnlyRootFilesystem: false
          runAsNonRoot: true
          runAsUser: 1001
          capabilities:
            drop:
            - ALL
        resources:
          limits:
            memory: "1Gi"
            cpu: "500m"
          requests:
            memory: "512Mi"
            cpu: "250m"
      volumes:
      - name: detector-code
        configMap:
          name: anomaly-detector-code
      - name: model-storage
        persistentVolumeClaim:
          claimName: anomaly-model-pvc
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: anomaly-detector-code
  namespace: security
data:
  anomaly-detection.py: |
    # 上記のPythonコードをここに配置
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: anomaly-model-pvc
  namespace: security
spec:
  accessModes:
  - ReadWriteOnce
  resources:
    requests:
      storage: 1Gi
EOF
```

## 🚨 Step 3: インシデント対応システム

### 3.1 自動化されたインシデント対応

```bash
# インシデント対応スクリプト
cat << 'EOF' > incident-response.sh
#!/bin/bash

# インシデント対応設定
INCIDENT_LOG="/var/log/security-incidents.log"
QUARANTINE_NAMESPACE="quarantine"
BACKUP_NAMESPACE="backup"

# ログ設定
log_incident() {
    local level=$1
    local message=$2
    local timestamp=$(date -u '+%Y-%m-%d %H:%M:%S UTC')
    echo "[$timestamp] [$level] $message" | tee -a $INCIDENT_LOG
}

# 緊急時コンテナ隔離
quarantine_container() {
    local namespace=$1
    local pod_name=$2
    local container_name=$3
    local incident_id=$4
    
    log_incident "INFO" "Starting quarantine process for $namespace/$pod_name/$container_name (Incident: $incident_id)"
    
    # Quarantine namespace作成
    kubectl create namespace $QUARANTINE_NAMESPACE --dry-run=client -o yaml | kubectl apply -f -
    
    # Network Policy でネットワーク隔離
    cat << YAML | kubectl apply -f -
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: quarantine-$incident_id
  namespace: $QUARANTINE_NAMESPACE
spec:
  podSelector:
    matchLabels:
      quarantine-id: "$incident_id"
  policyTypes:
  - Ingress
  - Egress
  # すべての通信を遮断
YAML
    
    # Pod の情報をバックアップ
    kubectl get pod $pod_name -n $namespace -o yaml > /tmp/quarantine-$incident_id-pod.yaml
    
    # Pod に隔離ラベル追加
    kubectl label pod $pod_name -n $namespace quarantine-id=$incident_id --overwrite
    kubectl label pod $pod_name -n $namespace quarantine-timestamp=$(date +%s) --overwrite
    
    # ログ出力のリダイレクト
    kubectl logs $pod_name -n $namespace -c $container_name > /tmp/quarantine-$incident_id-logs.txt
    
    log_incident "WARNING" "Container $namespace/$pod_name/$container_name quarantined with ID: $incident_id"
    
    # アラート送信
    send_incident_alert "QUARANTINE" "Container quarantined: $namespace/$pod_name/$container_name" "$incident_id"
}

# プロセス強制停止
kill_malicious_process() {
    local namespace=$1
    local pod_name=$2
    local process_name=$3
    local incident_id=$4
    
    log_incident "WARNING" "Killing malicious process: $process_name in $namespace/$pod_name (Incident: $incident_id)"
    
    # コンテナ内でプロセス強制停止
    kubectl exec $pod_name -n $namespace -- pkill -f "$process_name" || true
    
    # プロセス情報を記録
    kubectl exec $pod_name -n $namespace -- ps aux > /tmp/incident-$incident_id-processes.txt || true
    
    log_incident "INFO" "Process kill attempted for $process_name (Incident: $incident_id)"
}

# 証拠保全
preserve_evidence() {
    local namespace=$1
    local pod_name=$2
    local incident_id=$3
    
    log_incident "INFO" "Starting evidence preservation for $namespace/$pod_name (Incident: $incident_id)"
    
    local evidence_dir="/var/evidence/incident-$incident_id"
    mkdir -p $evidence_dir
    
    # Pod 定義の保存
    kubectl get pod $pod_name -n $namespace -o yaml > $evidence_dir/pod-definition.yaml
    
    # ログの保存
    kubectl logs $pod_name -n $namespace --all-containers=true > $evidence_dir/container-logs.txt
    
    # イベントの保存
    kubectl get events -n $namespace --field-selector involvedObject.name=$pod_name -o yaml > $evidence_dir/events.yaml
    
    # ネットワーク接続情報
    kubectl exec $pod_name -n $namespace -- netstat -tuln > $evidence_dir/network-connections.txt 2>/dev/null || true
    
    # プロセス情報
    kubectl exec $pod_name -n $namespace -- ps auxww > $evidence_dir/processes.txt 2>/dev/null || true
    
    # ファイルシステム情報
    kubectl exec $pod_name -n $namespace -- find /tmp /var/tmp -type f -ls > $evidence_dir/temp-files.txt 2>/dev/null || true
    
    # メタデータ
    cat > $evidence_dir/metadata.json << JSON
{
  "incident_id": "$incident_id",
  "namespace": "$namespace",
  "pod_name": "$pod_name",
  "timestamp": "$(date -u -Iseconds)",
  "kubernetes_version": "$(kubectl version --short --client)",
  "node_info": "$(kubectl get pod $pod_name -n $namespace -o jsonpath='{.spec.nodeName}')"
}
JSON
    
    # 証拠ファイルのハッシュ値計算
    find $evidence_dir -type f -exec sha256sum {} \; > $evidence_dir/file-hashes.txt
    
    log_incident "INFO" "Evidence preserved in $evidence_dir (Incident: $incident_id)"
}

# ワークロード一時停止
pause_workload() {
    local namespace=$1
    local workload_type=$2
    local workload_name=$3
    local incident_id=$4
    
    log_incident "WARNING" "Pausing workload: $workload_type/$workload_name in $namespace (Incident: $incident_id)"
    
    case $workload_type in
        "deployment")
            kubectl scale deployment $workload_name --replicas=0 -n $namespace
            ;;
        "daemonset")
            kubectl patch daemonset $workload_name -n $namespace -p '{"spec":{"template":{"spec":{"nodeSelector":{"non-existing-node":"true"}}}}}'
            ;;
        "statefulset")
            kubectl scale statefulset $workload_name --replicas=0 -n $namespace
            ;;
    esac
    
    log_incident "INFO" "Workload $workload_type/$workload_name paused (Incident: $incident_id)"
}

# インシデントアラート送信
send_incident_alert() {
    local alert_type=$1
    local message=$2
    local incident_id=$3
    
    local alert_payload=$(cat << JSON
{
  "rule": "Incident Response: $alert_type",
  "priority": "CRITICAL",
  "time": "$(date -u -Iseconds)",
  "output_fields": {
    "incident.id": "$incident_id",
    "incident.type": "$alert_type",
    "incident.message": "$message",
    "response.timestamp": "$(date -u -Iseconds)"
  }
}
JSON
)
    
    # Webhook に送信
    curl -X POST \
         -H "Content-Type: application/json" \
         -d "$alert_payload" \
         http://security-webhook.security.svc.cluster.local:8080 \
         --max-time 10 --silent || true
}

# Falco アラート処理
process_falco_alert() {
    local alert_json=$1
    
    # JSON からフィールド抽出
    local rule=$(echo "$alert_json" | jq -r '.rule // "Unknown"')
    local priority=$(echo "$alert_json" | jq -r '.priority // "INFO"')
    local container_name=$(echo "$alert_json" | jq -r '.output_fields["container.name"] // "unknown"')
    local namespace=$(echo "$alert_json" | jq -r '.output_fields["k8s.ns.name"] // "default"')
    local pod_name=$(echo "$alert_json" | jq -r '.output_fields["k8s.pod.name"] // "unknown"')
    local proc_cmdline=$(echo "$alert_json" | jq -r '.output_fields["proc.cmdline"] // "unknown"')
    
    # インシデントID生成
    local incident_id="INC-$(date +%Y%m%d-%H%M%S)-$(openssl rand -hex 4)"
    
    log_incident "ALERT" "Processing Falco alert: $rule (Priority: $priority, Incident: $incident_id)"
    
    # 重要度に応じた対応
    case $priority in
        "CRITICAL")
            # 証拠保全
            preserve_evidence "$namespace" "$pod_name" "$incident_id"
            
            # 特定ルールに対する自動対応
            case $rule in
                *"Container Escape"*|*"Privilege Escalation"*)
                    quarantine_container "$namespace" "$pod_name" "$container_name" "$incident_id"
                    ;;
                *"Crypto Mining"*)
                    kill_malicious_process "$namespace" "$pod_name" "xmrig\|minerd\|cpuminer" "$incident_id"
                    ;;
                *"Data Exfiltration"*)
                    quarantine_container "$namespace" "$pod_name" "$container_name" "$incident_id"
                    ;;
            esac
            ;;
        "WARNING")
            preserve_evidence "$namespace" "$pod_name" "$incident_id"
            
            # 監視強化
            kubectl label pod $pod_name -n $namespace security-watch=enhanced --overwrite
            ;;
        "INFO")
            # ログ記録のみ
            log_incident "INFO" "Security event logged: $rule in $namespace/$pod_name"
            ;;
    esac
    
    # インシデント詳細をファイルに保存
    echo "$alert_json" > "/var/incidents/incident-$incident_id.json"
}

# メイン処理
main() {
    # 必要なディレクトリ作成
    mkdir -p /var/log /var/evidence /var/incidents
    
    # Falco アラートの監視（実際の実装では適切なイベントストリームを使用）
    log_incident "INFO" "Incident response system started"
    
    # 標準入力からJSON アラートを受信
    while IFS= read -r line; do
        if [[ $line == *"{"* ]]; then
            process_falco_alert "$line"
        fi
    done
}

# スクリプトが直接実行された場合
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
EOF

chmod +x incident-response.sh
```

### 3.2 インシデント対応 Deployment

```yaml
# インシデント対応システムのデプロイ
cat << 'EOF' > incident-response-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: incident-response
  namespace: security
spec:
  replicas: 1
  selector:
    matchLabels:
      app: incident-response
  template:
    metadata:
      labels:
        app: incident-response
    spec:
      serviceAccountName: incident-response
      containers:
      - name: incident-handler
        image: alpine:latest
        command:
        - /bin/sh
        - -c
        - |
          apk add --no-cache bash curl jq openssl kubectl
          chmod +x /scripts/incident-response.sh
          tail -f /dev/null  # Keep container running
        volumeMounts:
        - name: incident-scripts
          mountPath: /scripts
        - name: evidence-storage
          mountPath: /var/evidence
        - name: incident-logs
          mountPath: /var/log
        securityContext:
          allowPrivilegeEscalation: false
          readOnlyRootFilesystem: false
          runAsNonRoot: true
          runAsUser: 1001
          capabilities:
            drop:
            - ALL
        resources:
          limits:
            memory: "256Mi"
            cpu: "200m"
          requests:
            memory: "128Mi"
            cpu: "100m"
      volumes:
      - name: incident-scripts
        configMap:
          name: incident-response-scripts
          defaultMode: 0755
      - name: evidence-storage
        persistentVolumeClaim:
          claimName: evidence-pvc
      - name: incident-logs
        persistentVolumeClaim:
          claimName: incident-logs-pvc
---
apiVersion: v1
kind: ServiceAccount
metadata:
  name: incident-response
  namespace: security
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: incident-response-role
rules:
- apiGroups: [""]
  resources: ["pods", "pods/log", "pods/exec", "events", "namespaces"]
  verbs: ["get", "list", "watch", "create", "update", "patch", "delete"]
- apiGroups: ["apps"]
  resources: ["deployments", "daemonsets", "statefulsets"]
  verbs: ["get", "list", "watch", "update", "patch"]
- apiGroups: ["networking.k8s.io"]
  resources: ["networkpolicies"]
  verbs: ["get", "list", "watch", "create", "update", "patch", "delete"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: incident-response-binding
subjects:
- kind: ServiceAccount
  name: incident-response
  namespace: security
roleRef:
  kind: ClusterRole
  name: incident-response-role
  apiGroup: rbac.authorization.k8s.io
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: incident-response-scripts
  namespace: security
data:
  incident-response.sh: |
    # 上記のシェルスクリプトをここに配置
EOF

kubectl apply -f incident-response-deployment.yaml
```

## 📈 Step 4: セキュリティダッシュボードとレポート

### 4.1 包括的セキュリティダッシュボード

```yaml
# Grafana セキュリティダッシュボード
cat << 'EOF' > comprehensive-security-dashboard.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: security-dashboard
  namespace: monitoring
data:
  dashboard.json: |
    {
      "dashboard": {
        "id": null,
        "title": "Kubernetes Security Operations Center",
        "tags": ["security", "falco", "kubernetes"],
        "timezone": "browser",
        "panels": [
          {
            "id": 1,
            "title": "Security Alert Summary",
            "type": "stat",
            "gridPos": {"h": 8, "w": 12, "x": 0, "y": 0},
            "targets": [
              {
                "expr": "increase(falco_events_total[24h])",
                "legendFormat": "Total Alerts (24h)"
              },
              {
                "expr": "increase(falco_events_total{priority=\"Critical\"}[24h])",
                "legendFormat": "Critical Alerts (24h)"
              }
            ],
            "fieldConfig": {
              "defaults": {
                "color": {"mode": "palette-classic"},
                "unit": "short"
              }
            }
          },
          {
            "id": 2,
            "title": "Real-time Security Events",
            "type": "logs",
            "gridPos": {"h": 8, "w": 12, "x": 12, "y": 0},
            "targets": [
              {
                "expr": "{namespace=\"falco-system\"} |= \"Falco\"",
                "refId": "A"
              }
            ]
          },
          {
            "id": 3,
            "title": "Security Events by Priority",
            "type": "piechart",
            "gridPos": {"h": 8, "w": 6, "x": 0, "y": 8},
            "targets": [
              {
                "expr": "sum by (priority) (increase(falco_events_total[1h]))",
                "legendFormat": "{{priority}}"
              }
            ]
          },
          {
            "id": 4,
            "title": "Top Security Rules Triggered",
            "type": "table",
            "gridPos": {"h": 8, "w": 18, "x": 6, "y": 8},
            "targets": [
              {
                "expr": "topk(10, sum by (rule) (increase(falco_events_total[24h])))",
                "format": "table"
              }
            ]
          },
          {
            "id": 5,
            "title": "Container Security Violations",
            "type": "graph",
            "gridPos": {"h": 8, "w": 12, "x": 0, "y": 16},
            "targets": [
              {
                "expr": "sum by (container_name) (increase(falco_events_total{rule=~\".*Container.*\"}[1h]))",
                "legendFormat": "{{container_name}}"
              }
            ]
          },
          {
            "id": 6,
            "title": "Network Security Events",
            "type": "graph",
            "gridPos": {"h": 8, "w": 12, "x": 12, "y": 16},
            "targets": [
              {
                "expr": "sum by (rule) (increase(falco_events_total{rule=~\".*[Nn]etwork.*\"}[1h]))",
                "legendFormat": "{{rule}}"
              }
            ]
          },
          {
            "id": 7,
            "title": "Compliance Status",
            "type": "stat",
            "gridPos": {"h": 6, "w": 8, "x": 0, "y": 24},
            "targets": [
              {
                "expr": "100 - (increase(falco_events_total{priority=\"Critical\"}[24h]) / increase(falco_events_total[24h]) * 100)",
                "legendFormat": "Compliance Score (%)"
              }
            ],
            "fieldConfig": {
              "defaults": {
                "unit": "percent",
                "min": 0,
                "max": 100,
                "thresholds": {
                  "steps": [
                    {"color": "red", "value": 0},
                    {"color": "yellow", "value": 80},
                    {"color": "green", "value": 95}
                  ]
                }
              }
            }
          },
          {
            "id": 8,
            "title": "Incident Response Times",
            "type": "graph",
            "gridPos": {"h": 6, "w": 8, "x": 8, "y": 24},
            "targets": [
              {
                "expr": "histogram_quantile(0.95, rate(incident_response_duration_seconds_bucket[5m]))",
                "legendFormat": "95th percentile"
              },
              {
                "expr": "histogram_quantile(0.50, rate(incident_response_duration_seconds_bucket[5m]))",
                "legendFormat": "50th percentile"
              }
            ]
          },
          {
            "id": 9,
            "title": "Anomaly Detection Status",
            "type": "stat",
            "gridPos": {"h": 6, "w": 8, "x": 16, "y": 24},
            "targets": [
              {
                "expr": "up{job=\"anomaly-detector\"}",
                "legendFormat": "Anomaly Detector Status"
              }
            ],
            "fieldConfig": {
              "defaults": {
                "mappings": [
                  {"options": {"0": {"text": "DOWN", "color": "red"}}, "type": "value"},
                  {"options": {"1": {"text": "UP", "color": "green"}}, "type": "value"}
                ]
              }
            }
          }
        ],
        "time": {
          "from": "now-24h",
          "to": "now"
        },
        "refresh": "30s"
      }
    }
EOF

kubectl apply -f comprehensive-security-dashboard.yaml
```

### 4.2 セキュリティレポート生成

```bash
# 定期セキュリティレポート生成スクリプト
cat << 'EOF' > generate-security-report.sh
#!/bin/bash

REPORT_DATE=$(date '+%Y-%m-%d')
REPORT_DIR="/var/reports"
REPORT_FILE="$REPORT_DIR/security-report-$REPORT_DATE.html"

mkdir -p $REPORT_DIR

# HTMLレポート生成
cat << HTML > $REPORT_FILE
<!DOCTYPE html>
<html>
<head>
    <title>Kubernetes Security Report - $REPORT_DATE</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .header { background-color: #f0f0f0; padding: 20px; border-radius: 5px; }
        .section { margin: 20px 0; }
        .critical { color: red; font-weight: bold; }
        .warning { color: orange; font-weight: bold; }
        .info { color: blue; }
        .good { color: green; font-weight: bold; }
        table { border-collapse: collapse; width: 100%; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #f2f2f2; }
        .chart { margin: 20px 0; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🛡️ Kubernetes Security Report</h1>
        <p><strong>Report Date:</strong> $REPORT_DATE</p>
        <p><strong>Generated:</strong> $(date)</p>
    </div>

    <div class="section">
        <h2>📊 Executive Summary</h2>
        <ul>
            <li><strong>Total Security Events:</strong> <span id="total-events">Loading...</span></li>
            <li><strong>Critical Incidents:</strong> <span id="critical-incidents" class="critical">Loading...</span></li>
            <li><strong>Security Compliance Score:</strong> <span id="compliance-score">Loading...</span></li>
            <li><strong>Mean Time to Response:</strong> <span id="mttr">Loading...</span></li>
        </ul>
    </div>

    <div class="section">
        <h2>🚨 Security Incidents</h2>
        <table>
            <thead>
                <tr>
                    <th>Time</th>
                    <th>Severity</th>
                    <th>Rule</th>
                    <th>Container</th>
                    <th>Namespace</th>
                    <th>Status</th>
                </tr>
            </thead>
            <tbody id="incidents-table">
                <tr><td colspan="6">Loading incidents...</td></tr>
            </tbody>
        </table>
    </div>

    <div class="section">
        <h2>📈 Security Metrics</h2>
        <div class="chart">
            <canvas id="security-chart" width="800" height="400"></canvas>
        </div>
    </div>

    <div class="section">
        <h2>🔍 Anomaly Detection</h2>
        <table>
            <thead>
                <tr>
                    <th>Container</th>
                    <th>Anomaly Type</th>
                    <th>Score</th>
                    <th>Status</th>
                </tr>
            </thead>
            <tbody id="anomalies-table">
                <tr><td colspan="4">Loading anomalies...</td></tr>
            </tbody>
        </table>
    </div>

    <div class="section">
        <h2>🛠️ Remediation Actions</h2>
        <ul>
            <li><strong>High Priority:</strong>
                <ul id="high-priority-actions">
                    <li>Loading recommendations...</li>
                </ul>
            </li>
            <li><strong>Medium Priority:</strong>
                <ul id="medium-priority-actions">
                    <li>Loading recommendations...</li>
                </ul>
            </li>
        </ul>
    </div>

    <div class="section">
        <h2>📋 Compliance Status</h2>
        <table>
            <thead>
                <tr>
                    <th>Framework</th>
                    <th>Status</th>
                    <th>Score</th>
                    <th>Issues</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td>CIS Kubernetes Benchmark</td>
                    <td><span class="good">PASS</span></td>
                    <td>85%</td>
                    <td>3 minor issues</td>
                </tr>
                <tr>
                    <td>NIST Cybersecurity Framework</td>
                    <td><span class="warning">PARTIAL</span></td>
                    <td>78%</td>
                    <td>Logging improvements needed</td>
                </tr>
                <tr>
                    <td>SOC 2 Type II</td>
                    <td><span class="good">PASS</span></td>
                    <td>92%</td>
                    <td>1 documentation gap</td>
                </tr>
            </tbody>
        </table>
    </div>

    <div class="section">
        <h2>🔮 Recommendations</h2>
        <ol>
            <li><strong>Immediate Actions (0-24h):</strong>
                <ul>
                    <li>Review and remediate critical security alerts</li>
                    <li>Update security policies based on new threats</li>
                    <li>Enhance monitoring for detected anomalies</li>
                </ul>
            </li>
            <li><strong>Short-term Actions (1-7 days):</strong>
                <ul>
                    <li>Conduct security training for development teams</li>
                    <li>Implement additional network segmentation</li>
                    <li>Review and update incident response procedures</li>
                </ul>
            </li>
            <li><strong>Long-term Actions (1-4 weeks):</strong>
                <ul>
                    <li>Deploy additional security tools (SIEM integration)</li>
                    <li>Implement zero-trust network architecture</li>
                    <li>Establish regular penetration testing schedule</li>
                </ul>
            </li>
        </ol>
    </div>

    <div class="section">
        <h2>📞 Contact Information</h2>
        <p><strong>Security Team:</strong> security-team@company.com</p>
        <p><strong>On-call Engineer:</strong> +1-555-SECURITY</p>
        <p><strong>Incident Response:</strong> incidents@company.com</p>
    </div>

    <script>
        // データ取得とチャート描画のJavaScript
        async function loadSecurityData() {
            try {
                // Prometheusからデータを取得（実際の実装）
                const response = await fetch('/api/v1/query?query=falco_events_total');
                const data = await response.json();
                
                // データをHTMLに反映
                document.getElementById('total-events').textContent = data.total || '0';
                document.getElementById('critical-incidents').textContent = data.critical || '0';
                document.getElementById('compliance-score').textContent = data.compliance || '85%';
                document.getElementById('mttr').textContent = data.mttr || '15 minutes';
                
            } catch (error) {
                console.error('Failed to load security data:', error);
            }
        }
        
        // ページ読み込み時にデータを取得
        window.onload = loadSecurityData;
    </script>
</body>
</html>
HTML

echo "Security report generated: $REPORT_FILE"

# レポートをメール送信（オプション）
if command -v mail >/dev/null 2>&1; then
    echo "Sending security report via email..."
    mail -s "Kubernetes Security Report - $REPORT_DATE" \
         -a "Content-Type: text/html" \
         security-team@company.com < $REPORT_FILE
fi

# S3にアップロード（オプション）
if command -v aws >/dev/null 2>&1; then
    echo "Uploading report to S3..."
    aws s3 cp $REPORT_FILE s3://security-reports-bucket/kubernetes/$(basename $REPORT_FILE)
fi
EOF

chmod +x generate-security-report.sh
```

## 🧹 Step 5: クリーンアップ

```bash
# テスト用リソースの削除
kubectl delete namespace security --ignore-not-found
kubectl delete namespace falco-system --ignore-not-found
kubectl delete namespace quarantine --ignore-not-found

# Falco のアンインストール
helm uninstall falco -n falco-system --ignore-not-found

# ConfigMaps とスクリプトの削除
rm -f custom-falco-rules.yaml
rm -f security-webhook.yaml
rm -f anomaly-detection.py
rm -f incident-response.sh
rm -f generate-security-report.sh

echo "クリーンアップ完了"
```

## 💰 コスト計算

- **Falco**: 約200MB追加メモリ使用
- **異常検知システム**: 約1GB追加メモリ・CPU使用
- **インシデント対応**: 約100MB追加メモリ使用
- **ログストレージ**: 約10GB/月追加ストレージ
- **総追加コスト**: 月額約$75-150（クラスターサイズとログ量により変動）

## 📚 学習ポイント

### 重要な概念
1. **Runtime Security**: 実行時セキュリティ監視とリアルタイム脅威検知
2. **Behavioral Analysis**: 異常行動検知による未知の脅威対応
3. **Incident Response**: 自動化されたインシデント対応とフォレンジック
4. **Security Operations**: SOC（Security Operations Center）の運用
5. **Compliance Monitoring**: 継続的なコンプライアンス監視

### 実践的なスキル
- Falcoによる実行時セキュリティ監視の実装
- 機械学習を活用した異常検知システムの構築
- 自動化されたインシデント対応プロセスの構築
- セキュリティダッシュボードとレポートの作成
- エンタープライズレベルのセキュリティ運用

---

**🎉 CKS (Certified Kubernetes Security Specialist) 認定試験対策ラボ完了！**

この一連のラボを通じて、Kubernetesクラスターのセキュリティを包括的に学習しました。実際の認定試験では、これらの知識を組み合わせて複雑なセキュリティシナリオを解決する能力が求められます。継続的な学習と実践を通じて、Kubernetesセキュリティエキスパートとしてのスキルを向上させていきましょう。