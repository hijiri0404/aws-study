# Lab 3: システム堅牢化

## 🎯 学習目標

このラボでは、Kubernetesクラスターのシステムレベルでのセキュリティ堅牢化を実装します：

- ホストOSのセキュリティ強化
- kernel パラメータの最適化
- システムコール制限（seccomp/AppArmor）
- コンテナランタイムセキュリティ
- ファイルシステム保護

## 📋 前提条件

- Kubernetes クラスターが稼働中
- kubectl が設定済み
- sudo 権限を持つLinuxホストへのアクセス
- [Lab 2: クラスター堅牢化](./lab02-cluster-hardening.md) の完了推奨

## 🏗️ アーキテクチャ概要

```
┌─────────────────────────────────────────────────────────────┐
│                  システム堅牢化環境                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐     │
│  │   Host OS   │    │   Kernel    │    │ Container   │     │
│  │  Hardening  │    │ Security    │    │  Runtime    │     │
│  │             │    │             │    │  Security   │     │
│  └─────┬───────┘    └─────┬───────┘    └─────┬───────┘     │
│        │                  │                  │             │
│        ▼                  ▼                  ▼             │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │              System-level Security                     │ │
│  │     seccomp + AppArmor + SELinux + gVisor             │ │
│  └─────┬───────────────────────┬───────────────────────────┘ │
│        │                       │                             │
│        ▼                       ▼                             │
│  ┌─────────────┐         ┌─────────────┐                     │
│  │ Monitoring  │         │ Compliance  │                     │
│  │ & Auditing  │         │ Validation  │                     │
│  └─────────────┘         └─────────────┘                     │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 Step 1: ホストOS セキュリティ強化

### 1.1 システム更新とパッケージ管理

```bash
# システム全体のセキュリティアップデート
sudo apt update && sudo apt upgrade -y

# 不要なサービスの停止と無効化
cat << 'EOF' > disable-unnecessary-services.sh
#!/bin/bash

echo "=== Disabling Unnecessary Services ==="

# 不要なサービスリスト
SERVICES_TO_DISABLE=(
    "avahi-daemon"
    "cups"
    "nfs-common"
    "rpcbind"
    "telnet"
    "rsh-server"
    "ypbind"
    "tftp"
)

for service in "${SERVICES_TO_DISABLE[@]}"; do
    if systemctl is-enabled $service >/dev/null 2>&1; then
        echo "Disabling $service..."
        sudo systemctl disable $service
        sudo systemctl stop $service
    else
        echo "$service は既に無効化されています"
    fi
done

echo "=== Service Hardening Complete ==="
EOF

chmod +x disable-unnecessary-services.sh
./disable-unnecessary-services.sh
```

### 1.2 ファイルシステムセキュリティ

```bash
# セキュアマウントオプションの設定
cat << 'EOF' > secure-mount-options.sh
#!/bin/bash

echo "=== Configuring Secure Mount Options ==="

# /tmp を別パーティションとしてマウント（noexec, nosuid, nodev）
if ! grep -q "/tmp" /etc/fstab; then
    echo "tmpfs /tmp tmpfs defaults,rw,nosuid,nodev,noexec,relatime 0 0" | sudo tee -a /etc/fstab
fi

# /var/tmp を別パーティションとしてマウント
if ! grep -q "/var/tmp" /etc/fstab; then
    echo "tmpfs /var/tmp tmpfs defaults,rw,nosuid,nodev,noexec,relatime 0 0" | sudo tee -a /etc/fstab
fi

# /dev/shm を制限付きマウント
if ! grep -q "/dev/shm" /etc/fstab; then
    echo "tmpfs /dev/shm tmpfs defaults,noexec,nosuid,nodev 0 0" | sudo tee -a /etc/fstab
fi

echo "Mount options configured. Reboot required to take effect."

# ファイル権限の強化
sudo chmod 700 /root
sudo chmod 644 /etc/passwd
sudo chmod 644 /etc/group
sudo chmod 600 /etc/shadow
sudo chmod 600 /etc/gshadow

# システムファイルの不変設定
sudo chattr +i /etc/passwd
sudo chattr +i /etc/group
sudo chattr +i /etc/shadow
sudo chattr +i /etc/gshadow

echo "=== File System Security Applied ==="
EOF

chmod +x secure-mount-options.sh
./secure-mount-options.sh
```

### 1.3 カーネルパラメータの最適化

```bash
# セキュリティ関連カーネルパラメータの設定
cat << 'EOF' > /etc/sysctl.d/99-kubernetes-security.conf
# ネットワークセキュリティ
net.ipv4.ip_forward = 1
net.ipv4.conf.all.forwarding = 1
net.ipv6.conf.all.forwarding = 1
net.bridge.bridge-nf-call-iptables = 1
net.bridge.bridge-nf-call-ip6tables = 1

# IP スプーフィング保護
net.ipv4.conf.all.rp_filter = 1
net.ipv4.conf.default.rp_filter = 1

# ICMP リダイレクト無効化
net.ipv4.conf.all.accept_redirects = 0
net.ipv4.conf.default.accept_redirects = 0
net.ipv6.conf.all.accept_redirects = 0
net.ipv6.conf.default.accept_redirects = 0

# 送信リダイレクト無効化
net.ipv4.conf.all.send_redirects = 0
net.ipv4.conf.default.send_redirects = 0

# ソースルーティング無効化
net.ipv4.conf.all.accept_source_route = 0
net.ipv4.conf.default.accept_source_route = 0
net.ipv6.conf.all.accept_source_route = 0
net.ipv6.conf.default.accept_source_route = 0

# SYN Flood 攻撃保護
net.ipv4.tcp_syncookies = 1
net.ipv4.tcp_max_syn_backlog = 2048
net.ipv4.tcp_synack_retries = 2
net.ipv4.tcp_syn_retries = 5

# メモリ保護
kernel.dmesg_restrict = 1
kernel.kptr_restrict = 2
kernel.yama.ptrace_scope = 1

# コアダンプ制限
fs.suid_dumpable = 0
kernel.core_pattern = |/bin/false

# プロセス制限
kernel.pid_max = 65536
EOF

# カーネルパラメータを適用
sudo sysctl --system
```

## 🛡️ Step 2: seccomp プロファイルの実装

### 2.1 カスタムseccompプロファイル作成

```bash
# seccomp プロファイルディレクトリ作成
sudo mkdir -p /etc/kubernetes/seccomp-profiles

# 制限的なseccompプロファイル作成
cat << 'EOF' > /etc/kubernetes/seccomp-profiles/restricted-profile.json
{
    "defaultAction": "SCMP_ACT_ERRNO",
    "architectures": [
        "SCMP_ARCH_X86_64",
        "SCMP_ARCH_X86",
        "SCMP_ARCH_X32"
    ],
    "syscalls": [
        {
            "names": [
                "accept",
                "accept4",
                "access",
                "arch_prctl",
                "bind",
                "brk",
                "capget",
                "capset",
                "chdir",
                "chmod",
                "chown",
                "clock_getres",
                "clock_gettime",
                "clone",
                "close",
                "connect",
                "copy_file_range",
                "creat",
                "dup",
                "dup2",
                "dup3",
                "epoll_create",
                "epoll_create1",
                "epoll_ctl",
                "epoll_pwait",
                "epoll_wait",
                "eventfd",
                "eventfd2",
                "execve",
                "exit",
                "exit_group",
                "faccessat",
                "fadvise64",
                "fallocate",
                "fchdir",
                "fchmod",
                "fchmodat",
                "fchown",
                "fchownat",
                "fcntl",
                "fdatasync",
                "fgetxattr",
                "flistxattr",
                "flock",
                "fork",
                "fsetxattr",
                "fstat",
                "fstatfs",
                "fsync",
                "ftruncate",
                "futex",
                "getcwd",
                "getdents",
                "getdents64",
                "getegid",
                "geteuid",
                "getgid",
                "getgroups",
                "getpeername",
                "getpgrp",
                "getpid",
                "getppid",
                "getpriority",
                "getrandom",
                "getresgid",
                "getresuid",
                "getrlimit",
                "getrusage",
                "getsid",
                "getsockname",
                "getsockopt",
                "gettid",
                "gettimeofday",
                "getuid",
                "getxattr",
                "inotify_add_watch",
                "inotify_init",
                "inotify_init1",
                "inotify_rm_watch",
                "io_cancel",
                "io_destroy",
                "io_getevents",
                "io_setup",
                "io_submit",
                "ioctl",
                "kill",
                "lgetxattr",
                "link",
                "linkat",
                "listen",
                "listxattr",
                "llistxattr",
                "lseek",
                "lstat",
                "madvise",
                "memfd_create",
                "mkdir",
                "mkdirat",
                "mknod",
                "mknodat",
                "mlock",
                "mlock2",
                "mlockall",
                "mmap",
                "mprotect",
                "mq_getsetattr",
                "mq_notify",
                "mq_open",
                "mq_receive",
                "mq_send",
                "mq_timedreceive",
                "mq_timedsend",
                "mq_unlink",
                "mremap",
                "msgctl",
                "msgget",
                "msgrcv",
                "msgsnd",
                "msync",
                "munlock",
                "munlockall",
                "munmap",
                "nanosleep",
                "newfstatat",
                "open",
                "openat",
                "pause",
                "pipe",
                "pipe2",
                "poll",
                "ppoll",
                "prctl",
                "pread64",
                "prlimit64",
                "pselect6",
                "ptrace",
                "pwrite64",
                "read",
                "readlink",
                "readlinkat",
                "readv",
                "recv",
                "recvfrom",
                "recvmmsg",
                "recvmsg",
                "rename",
                "renameat",
                "renameat2",
                "restart_syscall",
                "rmdir",
                "rt_sigaction",
                "rt_sigpending",
                "rt_sigprocmask",
                "rt_sigqueueinfo",
                "rt_sigreturn",
                "rt_sigsuspend",
                "rt_sigtimedwait",
                "rt_tgsigqueueinfo",
                "sched_getaffinity",
                "sched_getattr",
                "sched_getparam",
                "sched_get_priority_max",
                "sched_get_priority_min",
                "sched_getscheduler",
                "sched_setaffinity",
                "sched_setattr",
                "sched_setparam",
                "sched_setscheduler",
                "sched_yield",
                "seccomp",
                "select",
                "semctl",
                "semget",
                "semop",
                "semtimedop",
                "send",
                "sendfile",
                "sendmmsg",
                "sendmsg",
                "sendto",
                "setfsgid",
                "setfsuid",
                "setgid",
                "setgroups",
                "setitimer",
                "setpgid",
                "setpriority",
                "setregid",
                "setresgid",
                "setresuid",
                "setreuid",
                "setrlimit",
                "setsid",
                "setsockopt",
                "setuid",
                "setxattr",
                "shmat",
                "shmctl",
                "shmdt",
                "shmget",
                "shutdown",
                "sigaltstack",
                "signalfd",
                "signalfd4",
                "sigreturn",
                "socket",
                "socketpair",
                "splice",
                "stat",
                "statfs",
                "symlink",
                "symlinkat",
                "sync",
                "sync_file_range",
                "syncfs",
                "sysinfo",
                "tee",
                "tgkill",
                "time",
                "timer_create",
                "timer_delete",
                "timer_getoverrun",
                "timer_gettime",
                "timer_settime",
                "timerfd_create",
                "timerfd_gettime",
                "timerfd_settime",
                "times",
                "tkill",
                "truncate",
                "umask",
                "uname",
                "unlink",
                "unlinkat",
                "utime",
                "utimensat",
                "utimes",
                "vfork",
                "vmsplice",
                "wait4",
                "waitid",
                "write",
                "writev"
            ],
            "action": "SCMP_ACT_ALLOW"
        }
    ]
}
EOF

# Web アプリケーション用のseccompプロファイル
cat << 'EOF' > /etc/kubernetes/seccomp-profiles/webapp-profile.json
{
    "defaultAction": "SCMP_ACT_ERRNO",
    "architectures": [
        "SCMP_ARCH_X86_64",
        "SCMP_ARCH_X86",
        "SCMP_ARCH_X32"
    ],
    "syscalls": [
        {
            "names": [
                "accept",
                "accept4",
                "bind",
                "brk",
                "close",
                "connect",
                "dup",
                "dup2",
                "epoll_create",
                "epoll_create1",
                "epoll_ctl",
                "epoll_wait",
                "execve",
                "exit",
                "exit_group",
                "fcntl",
                "fstat",
                "futex",
                "getpid",
                "getsockname",
                "getsockopt",
                "gettid",
                "gettimeofday",
                "listen",
                "lseek",
                "mmap",
                "mprotect",
                "munmap",
                "open",
                "openat",
                "poll",
                "read",
                "recv",
                "recvfrom",
                "rt_sigaction",
                "rt_sigprocmask",
                "rt_sigreturn",
                "send",
                "sendto",
                "setsockopt",
                "shutdown",
                "socket",
                "stat",
                "write"
            ],
            "action": "SCMP_ACT_ALLOW"
        }
    ]
}
EOF

echo "seccomp プロファイル作成完了"
```

### 2.2 seccomp対応Pod作成

```yaml
# seccomp を使用するPod例
cat << 'EOF' > seccomp-pod-example.yaml
apiVersion: v1
kind: Pod
metadata:
  name: seccomp-restricted-pod
  namespace: production
spec:
  securityContext:
    seccompProfile:
      type: Localhost
      localhostProfile: restricted-profile.json
  containers:
  - name: secure-container
    image: nginx:1.21-alpine
    securityContext:
      allowPrivilegeEscalation: false
      readOnlyRootFilesystem: true
      runAsNonRoot: true
      runAsUser: 1001
      capabilities:
        drop:
        - ALL
    resources:
      limits:
        memory: "128Mi"
        cpu: "100m"
      requests:
        memory: "64Mi"
        cpu: "50m"
    volumeMounts:
    - name: tmp-volume
      mountPath: /tmp
    - name: cache-volume
      mountPath: /var/cache/nginx
    - name: run-volume
      mountPath: /var/run
  volumes:
  - name: tmp-volume
    emptyDir: {}
  - name: cache-volume
    emptyDir: {}
  - name: run-volume
    emptyDir: {}
---
# Webアプリケーション用Pod
apiVersion: v1
kind: Pod
metadata:
  name: webapp-seccomp-pod
  namespace: production
spec:
  securityContext:
    seccompProfile:
      type: Localhost
      localhostProfile: webapp-profile.json
  containers:
  - name: webapp
    image: nginx:1.21-alpine
    securityContext:
      allowPrivilegeEscalation: false
      readOnlyRootFilesystem: true
      runAsNonRoot: true
      runAsUser: 1001
      capabilities:
        drop:
        - ALL
    ports:
    - containerPort: 8080
    volumeMounts:
    - name: tmp-volume
      mountPath: /tmp
  volumes:
  - name: tmp-volume
    emptyDir: {}
EOF

kubectl apply -f seccomp-pod-example.yaml
```

## 🔒 Step 3: AppArmor プロファイルの実装

### 3.1 AppArmor プロファイル作成

```bash
# AppArmor がインストールされているか確認
sudo apt install apparmor-utils -y

# Kubernetes用AppArmorプロファイルディレクトリ作成
sudo mkdir -p /etc/apparmor.d/kubernetes

# 制限的なAppArmorプロファイル作成
cat << 'EOF' > /etc/apparmor.d/kubernetes/k8s-restricted-profile
#include <tunables/global>

profile k8s-restricted-profile flags=(audit,attach_disconnected,mediate_deleted) {
  #include <abstractions/base>

  # ファイルアクセス制限
  /bin/** rx,
  /usr/bin/** rx,
  /usr/lib/** rx,
  /lib/** rx,
  /lib64/** rx,
  
  # 書き込み可能領域（制限付き）
  /tmp/** rw,
  /var/tmp/** rw,
  /dev/null rw,
  /dev/zero r,
  /dev/random r,
  /dev/urandom r,
  
  # プロセス制御
  /proc/*/stat r,
  /proc/*/status r,
  /proc/*/cmdline r,
  /proc/sys/kernel/version r,
  
  # ネットワーク制限
  network inet stream,
  network inet dgram,
  network inet6 stream,
  network inet6 dgram,
  
  # 危険な操作を明示的に拒否
  deny /etc/shadow r,
  deny /etc/passwd w,
  deny /etc/group w,
  deny /boot/** rw,
  deny /sys/** w,
  deny mount,
  deny umount,
  deny capability sys_admin,
  deny capability sys_module,
  deny capability dac_override,
  deny capability dac_read_search,
  deny capability setuid,
  deny capability setgid,
  deny ptrace,
  
  # ログファイルアクセス制限
  deny /var/log/** w,
  
  # システムコール制限
  deny @{PROC}/sys/kernel/core_pattern w,
  deny @{PROC}/sys/vm/mmap_min_addr w,
}
EOF

# プロファイルをロード
sudo apparmor_parser -r /etc/apparmor.d/kubernetes/k8s-restricted-profile

# Web アプリケーション用プロファイル
cat << 'EOF' > /etc/apparmor.d/kubernetes/k8s-webapp-profile
#include <tunables/global>

profile k8s-webapp-profile flags=(audit,attach_disconnected,mediate_deleted) {
  #include <abstractions/base>

  # 基本的な実行権限
  /bin/** rx,
  /usr/bin/** rx,
  /usr/lib/** rx,
  /lib/** rx,
  /lib64/** rx,
  
  # Web サーバー固有のパス
  /usr/share/nginx/** r,
  /etc/nginx/** r,
  /var/log/nginx/** w,
  /var/cache/nginx/** rw,
  /run/nginx.pid rw,
  
  # 一時ファイル領域
  /tmp/** rw,
  /var/tmp/** rw,
  
  # プロセス制御（制限付き）
  /proc/*/stat r,
  /proc/*/status r,
  /proc/sys/kernel/version r,
  
  # ネットワーク（HTTP/HTTPS のみ）
  network inet stream,
  network inet dgram,
  
  # 明示的な拒否
  deny /etc/shadow r,
  deny /etc/passwd w,
  deny /boot/** rw,
  deny /sys/** w,
  deny mount,
  deny umount,
  deny capability sys_admin,
  deny capability sys_module,
  deny ptrace,
}
EOF

sudo apparmor_parser -r /etc/apparmor.d/kubernetes/k8s-webapp-profile

echo "AppArmor プロファイル作成・ロード完了"
```

### 3.2 AppArmor対応Pod作成

```yaml
# AppArmor を使用するPod例
cat << 'EOF' > apparmor-pod-example.yaml
apiVersion: v1
kind: Pod
metadata:
  name: apparmor-restricted-pod
  namespace: production
  annotations:
    container.apparmor.security.beta.kubernetes.io/secure-container: localhost/k8s-restricted-profile
spec:
  containers:
  - name: secure-container
    image: alpine:3.14
    command: ["/bin/sh"]
    args: ["-c", "while true; do echo 'AppArmor制限付きコンテナ実行中'; sleep 30; done"]
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
kind: Pod
metadata:
  name: apparmor-webapp-pod
  namespace: production
  annotations:
    container.apparmor.security.beta.kubernetes.io/webapp: localhost/k8s-webapp-profile
spec:
  containers:
  - name: webapp
    image: nginx:1.21-alpine
    securityContext:
      allowPrivilegeEscalation: false
      runAsNonRoot: true
      runAsUser: 101
      capabilities:
        drop:
        - ALL
    ports:
    - containerPort: 80
EOF

kubectl apply -f apparmor-pod-example.yaml
```

## ⚡ Step 4: gVisor（コンテナサンドボックス）の実装

### 4.1 gVisor インストール

```bash
# gVisor (runsc) インストール
curl -fsSL https://gvisor.dev/archive.key | sudo gpg --dearmor -o /usr/share/keyrings/gvisor-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/gvisor-archive-keyring.gpg] https://storage.googleapis.com/gvisor/releases release main" | sudo tee /etc/apt/sources.list.d/gvisor.list > /dev/null

sudo apt update && sudo apt install -y runsc

# containerd 設定でgVisorランタイムを追加
sudo tee -a /etc/containerd/config.toml > /dev/null <<EOF

[plugins."io.containerd.grpc.v1.cri".containerd.runtimes.runsc]
  runtime_type = "io.containerd.runsc.v1"

[plugins."io.containerd.grpc.v1.cri".containerd.runtimes.runsc.options]
  TypeUrl = "io.containerd.runsc.v1.options"
  ConfigPath = "/etc/containerd/runsc.toml"
EOF

# runsc 設定ファイル作成
sudo tee /etc/containerd/runsc.toml > /dev/null <<EOF
[runsc_config]
debug = false
debug-log = "/tmp/runsc-debug.log"
strace = false
platform = "ptrace"
file-access = "exclusive"
overlay = false
network = "sandbox"
log-packets = false
num-network-channels = 1
rootless = false
alsologtostderr = false
ref-leak-mode = "disabled"
EOF

# containerd 再起動
sudo systemctl restart containerd

echo "gVisor インストール完了"
```

### 4.2 RuntimeClass作成

```yaml
# gVisor用 RuntimeClass
cat << 'EOF' > gvisor-runtime-class.yaml
apiVersion: node.k8s.io/v1
kind: RuntimeClass
metadata:
  name: gvisor
handler: runsc
overhead:
  podFixed:
    memory: "200Mi"
    cpu: "0.1"
---
# gVisor を使用するPod例
apiVersion: v1
kind: Pod
metadata:
  name: gvisor-secure-pod
  namespace: production
spec:
  runtimeClassName: gvisor
  containers:
  - name: secure-app
    image: nginx:1.21-alpine
    securityContext:
      allowPrivilegeEscalation: false
      readOnlyRootFilesystem: true
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
    volumeMounts:
    - name: tmp-volume
      mountPath: /tmp
    - name: cache-volume
      mountPath: /var/cache/nginx
  volumes:
  - name: tmp-volume
    emptyDir: {}
  - name: cache-volume
    emptyDir: {}
EOF

kubectl apply -f gvisor-runtime-class.yaml
```

## 📊 Step 5: システムレベル監査とコンプライアンス

### 5.1 システム監査スクリプト

```bash
# 包括的システムセキュリティ監査スクリプト
cat << 'EOF' > system-security-audit.sh
#!/bin/bash

echo "=== システムセキュリティ監査 ==="
echo "監査実行日時: $(date)"
echo ""

# 1. OS セキュリティ確認
echo "1. オペレーティングシステム セキュリティ:"
echo "  OS バージョン: $(lsb_release -d | cut -f2)"
echo "  カーネルバージョン: $(uname -r)"
echo "  最後のアップデート: $(stat -c %y /var/log/apt/history.log | cut -d' ' -f1)"

# セキュリティアップデートの確認
SECURITY_UPDATES=$(apt list --upgradable 2>/dev/null | grep -i security | wc -l)
echo "  利用可能なセキュリティアップデート: $SECURITY_UPDATES"

echo ""

# 2. ファイルシステムセキュリティ
echo "2. ファイルシステム セキュリティ:"
echo "  /tmp のマウントオプション:"
mount | grep " /tmp " | awk '{print "    " $6}'

echo "  /var/tmp のマウントオプション:"
mount | grep " /var/tmp " | awk '{print "    " $6}'

echo "  重要ファイルの権限:"
ls -la /etc/passwd /etc/shadow /etc/group /etc/gshadow | awk '{print "    " $1 " " $9}'

echo ""

# 3. サービス確認
echo "3. 実行中サービス セキュリティ:"
echo "  不要な可能性があるサービス:"
systemctl list-units --type=service --state=running | grep -E "(telnet|ftp|tftp|rsh|rlogin)" | awk '{print "    " $1}' || echo "    問題となるサービスは見つかりませんでした"

echo ""

# 4. ネットワークセキュリティ
echo "4. ネットワーク セキュリティ:"
echo "  開いているポート:"
ss -tuln | grep LISTEN | awk '{print "    " $1 " " $5}' | sort | uniq

echo ""

# 5. カーネルセキュリティ
echo "5. カーネル セキュリティ設定:"
echo "  重要なsysctlパラメータ:"
for param in net.ipv4.ip_forward net.ipv4.conf.all.rp_filter kernel.dmesg_restrict kernel.kptr_restrict; do
    value=$(sysctl -n $param 2>/dev/null)
    echo "    $param = $value"
done

echo ""

# 6. AppArmor/SELinux 確認
echo "6. MAC (Mandatory Access Control) セキュリティ:"
if command -v aa-status >/dev/null 2>&1; then
    echo "  AppArmor ステータス:"
    aa-status --enabled && echo "    AppArmor: 有効" || echo "    AppArmor: 無効"
    APPARMOR_PROFILES=$(aa-status 2>/dev/null | grep "profiles are loaded" | awk '{print $1}')
    echo "    ロード済みプロファイル数: $APPARMOR_PROFILES"
fi

if command -v sestatus >/dev/null 2>&1; then
    echo "  SELinux ステータス:"
    sestatus | head -1 | awk '{print "    " $0}'
fi

echo ""

# 7. Kubernetes セキュリティ
echo "7. Kubernetes セキュリティ:"
if command -v kubectl >/dev/null 2>&1; then
    echo "  RuntimeClass の状態:"
    kubectl get runtimeclass 2>/dev/null | tail -n +2 | awk '{print "    " $1}' || echo "    RuntimeClass が見つかりません"
    
    echo "  seccomp プロファイル:"
    if [ -d "/etc/kubernetes/seccomp-profiles" ]; then
        ls /etc/kubernetes/seccomp-profiles/ | awk '{print "    " $1}' || echo "    seccomp プロファイルが見つかりません"
    else
        echo "    seccomp プロファイルディレクトリが存在しません"
    fi
fi

echo ""

# 8. コンテナランタイム セキュリティ
echo "8. コンテナランタイム セキュリティ:"
if systemctl is-active containerd >/dev/null 2>&1; then
    echo "  containerd: 実行中"
    if command -v ctr >/dev/null 2>&1; then
        RUNTIME_COUNT=$(ctr plugins ls 2>/dev/null | grep -c runtime || echo "0")
        echo "    利用可能なランタイム数: $RUNTIME_COUNT"
    fi
else
    echo "  containerd: 停止中"
fi

echo ""

# 9. 推奨事項
echo "=== セキュリティ推奨事項 ==="
echo "  - 定期的なセキュリティアップデートの適用"
echo "  - 不要なサービスの無効化"
echo "  - ファイアウォール設定の確認"
echo "  - ログ監視の実装"
echo "  - 侵入検知システムの導入検討"
echo "  - バックアップ戦略の確認"

echo ""
echo "=== 監査完了 ==="
EOF

chmod +x system-security-audit.sh
./system-security-audit.sh
```

### 5.2 継続的システム監視

```yaml
# システム監査CronJob
cat << 'EOF' > system-audit-cronjob.yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: system-security-audit
  namespace: kube-system
spec:
  schedule: "0 6 * * *"  # 毎日午前6時
  jobTemplate:
    spec:
      template:
        spec:
          hostPID: true
          hostNetwork: true
          serviceAccountName: system-audit-sa
          containers:
          - name: audit-container
            image: ubuntu:20.04
            command:
            - /bin/bash
            - -c
            - |
              apt update && apt install -y curl
              # システム監査スクリプトを実行
              curl -s https://raw.githubusercontent.com/your-repo/system-audit.sh | bash
            securityContext:
              privileged: true
            volumeMounts:
            - name: host-root
              mountPath: /host
              readOnly: true
            - name: audit-results
              mountPath: /results
          volumes:
          - name: host-root
            hostPath:
              path: /
          - name: audit-results
            persistentVolumeClaim:
              claimName: audit-results-pvc
          restartPolicy: OnFailure
---
apiVersion: v1
kind: ServiceAccount
metadata:
  name: system-audit-sa
  namespace: kube-system
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: system-audit-role
rules:
- apiGroups: [""]
  resources: ["nodes", "pods", "services"]
  verbs: ["get", "list"]
- apiGroups: ["apps"]
  resources: ["deployments", "daemonsets"]
  verbs: ["get", "list"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: system-audit-binding
subjects:
- kind: ServiceAccount
  name: system-audit-sa
  namespace: kube-system
roleRef:
  kind: ClusterRole
  name: system-audit-role
  apiGroup: rbac.authorization.k8s.io
EOF

kubectl apply -f system-audit-cronjob.yaml
```

## 🧹 Step 6: クリーンアップ

```bash
# テスト用リソースの削除
kubectl delete pod seccomp-restricted-pod webapp-seccomp-pod -n production --ignore-not-found
kubectl delete pod apparmor-restricted-pod apparmor-webapp-pod -n production --ignore-not-found
kubectl delete pod gvisor-secure-pod -n production --ignore-not-found
kubectl delete runtimeclass gvisor --ignore-not-found

# AppArmor プロファイルのアンロード（必要に応じて）
# sudo apparmor_parser -R /etc/apparmor.d/kubernetes/k8s-restricted-profile
# sudo apparmor_parser -R /etc/apparmor.d/kubernetes/k8s-webapp-profile

echo "クリーンアップ完了"
```

## 💰 コスト計算

このラボは既存のKubernetesクラスター内での設定変更が中心のため、追加コストは発生しません。gVisorによる若干のオーバーヘッドが生じる可能性があります。

## 📚 学習ポイント

### 重要な概念
1. **システムレベルセキュリティ**: ホストOSからコンテナまでの包括的な防御
2. **多層防御**: seccomp、AppArmor、gVisorの組み合わせ
3. **最小権限の原則**: システムコール制限による攻撃面の縮小
4. **ゼロトラスト**: コンテナサンドボックスによる分離
5. **継続的監視**: 自動化されたセキュリティ監査

### 実践的なスキル
- ホストOSのセキュリティ強化設定
- seccompプロファイルの作成と適用
- AppArmorプロファイルの実装
- gVisorによるコンテナサンドボックス化
- システムレベルセキュリティ監査の自動化

---

**次のステップ**: [Lab 4: マイクロサービスセキュリティ](./lab04-microservice-security.md) では、マイクロサービス間の通信セキュリティを学習します。