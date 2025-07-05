# AWS Certified DevOps Engineer Professional (DOP-C02) 想定問題集

## 📋 試験について

- **問題数**: 100問（実際の試験は75問）
- **制限時間**: 180分
- **合格点**: 750/1000点
- **形式**: 選択問題（単一選択・複数選択）

## 🎯 Domain 1: SDLC Automation (22%) - 問題1-22

### 問題1
あなたの会社では、マイクロサービスアーキテクチャを採用しており、複数のサービスが独立してデプロイされる必要があります。各サービスは独自のリポジトリを持ち、異なる開発チームが管理しています。最も効率的なCI/CDパイプライン戦略は何ですか？

A) 全サービスを単一のCodePipelineで管理し、順次デプロイを実行する  
B) 各サービスに独立したCodePipelineを作成し、並列デプロイを可能にする  
C) GitLab CIを使用して、AWSサービスを完全に回避する  
D) 手動デプロイプロセスを維持し、エラーが発生した場合のみ自動化を検討する

**正解**: B  
**解説**: マイクロサービスアーキテクチャでは、各サービスの独立性が重要です。独立したパイプラインにより、開発チームは他のサービスに影響を与えることなく、迅速にデプロイできます。

### 問題2
CodeBuildプロジェクトで、ビルドプロセス中に機密情報（データベースパスワード、APIキー）を安全に使用する最適な方法は？

A) buildspec.ymlファイルに直接記述する  
B) Systems Manager Parameter Store から環境変数として取得する  
C) S3バケットに保存し、ビルド時にダウンロードする  
D) Git リポジトリの .env ファイルに保存する

**正解**: B  
**解説**: Systems Manager Parameter Store（またはSecrets Manager）は、機密情報を安全に保存し、IAM権限で制御された方法でアクセスできます。buildspec.ymlで environment セクションを使用して取得できます。

### 問題3
CodePipelineで、本番環境への自動デプロイ前に手動承認ステップを追加したいと考えています。適切な設定方法は？

A) CodeCommitで承認機能を有効にする  
B) Manual approval actionをパイプラインに追加する  
C) Lambda関数で承認ロジックを実装する  
D) CloudFormation change setsを使用する

**正解**: B  
**解説**: CodePipelineのManual approval actionを使用することで、指定したIAMユーザーまたはロールが承認するまでパイプラインを一時停止できます。

### 問題4
複数環境（開発、ステージング、本番）でのデプロイ戦略として、環境ごとに異なる設定を管理する最適な方法は？

A) 環境ごとに別々のGitリポジトリを作成する  
B) CodeDeployのdeployment configurationsを環境ごとに作成する  
C) Systems Manager Parameter Storeで環境ごとの設定を管理し、デプロイ時に動的に取得する  
D) 各環境でハードコードされた設定ファイルを使用する

**正解**: C  
**解説**: Parameter Storeを使用して環境ごとの設定を一元管理することで、同一のアプリケーションコードで複数環境にデプロイでき、設定の変更も容易になります。

### 問題5
CodeDeployでBlue/Green deploymentを実装する際の主要な利点は？

A) デプロイメント時間の短縮  
B) ダウンタイムなしでのデプロイとロールバック機能  
C) インフラストラクチャコストの削減  
D) セキュリティの向上

**正解**: B  
**解説**: Blue/Green deploymentは、現行バージョン（Blue）を稼働させながら新バージョン（Green）をデプロイし、切り替え時のダウンタイムを最小化できます。また、問題発生時の即座のロールバックが可能です。

## 🎯 Domain 2: Configuration Management and IaC (17%) - 問題23-39

### 問題23
CloudFormationで大規模なインフラストラクチャを管理する際、スタックの依存関係を適切に管理する方法は？

A) 単一の巨大なテンプレートファイルを作成する  
B) Nested stacksまたはCross-stack referencesを使用する  
C) 手動でリソースを作成し、CloudFormationでインポートする  
D) Terraformに移行する

**正解**: B  
**解説**: Nested stacksやCross-stack references（Export/ImportValue）を使用することで、スタック間の依存関係を明示的に管理でき、再利用性と保守性が向上します。

### 問題24
AWS CDKの主要な利点は何ですか？

A) CloudFormationより高速なデプロイ  
B) プログラミング言語での型安全性とIDEサポート  
C) より安価なデプロイメント  
D) JSONおよびYAMLのサポート

**正解**: B  
**解説**: CDKは、TypeScript、Python、Javaなどのプログラミング言語を使用してインフラストラクチャを定義でき、型安全性、自動補完、リファクタリングなどのIDEの利点を活用できます。

### 問題25
Systems Manager Session Managerの主要な利点は？

A) SSH接続の高速化  
B) EC2インスタンスへのセキュアなアクセス（SSH鍵不要、ポート開放不要）  
C) インスタンスのパフォーマンス向上  
D) ログの自動収集

**正解**: B  
**解説**: Session Managerは、SSH鍵の管理やセキュリティグループでのポート開放が不要で、IAM権限のみでEC2インスタンスにセキュアにアクセスできます。全セッションはCloudTrailに記録されます。

## 🎯 Domain 3: Resilient Cloud Solutions (15%) - 問題40-51

### 問題40
マルチAZ構成のRDSインスタンスで自動フェイルオーバーが発生する条件は？

A) CPU使用率が90%を超えた場合  
B) プライマリインスタンスの計画メンテナンス  
C) プライマリインスタンスの障害またはAZ障害  
D) ディスク容量が不足した場合

**正解**: C  
**解説**: マルチAZ RDSは、プライマリインスタンスまたはAZ レベルの障害時に自動的にスタンバイインスタンスにフェイルオーバーします。計画メンテナンス時は事前にフェイルオーバーが実行されます。

### 問題41
Auto Scalingグループで、新しくプロビジョニングされたインスタンスがロードバランサーのヘルスチェックに失敗し続ける場合の対処法は？

A) Health check grace periodを延長する  
B) インスタンスタイプを変更する  
C) Auto Scalingを無効にする  
D) ヘルスチェックを無効にする

**正解**: A  
**解説**: Health check grace periodを適切に設定することで、アプリケーションの起動に十分な時間を与えることができます。デフォルトは300秒ですが、アプリケーションの起動時間に応じて調整が必要です。

## 🎯 Domain 4: Monitoring and Logging (15%) - 問題52-63

### 問題52
CloudWatch Logsで大量のログデータを効率的に分析する方法は？

A) 手動でログファイルをダウンロードして分析  
B) CloudWatch Insights を使用したクエリベース分析  
C) S3にエクスポートしてExcelで分析  
D) CloudTrailと連携して分析

**正解**: B  
**解説**: CloudWatch Insightsは、SQLライクなクエリ言語を使用して、CloudWatch Logsのデータを効率的に検索、分析、可視化できます。

### 問題53
X-Rayを使用した分散トレーシングの主要な目的は？

A) アプリケーションのセキュリティ向上  
B) マイクロサービス間のリクエストフローとパフォーマンスの可視化  
C) ログの集中管理  
D) アプリケーションの自動復旧

**正解**: B  
**解説**: X-Rayは、分散システムでのリクエストの流れ、各コンポーネントでの実行時間、エラーの発生箇所を可視化し、パフォーマンスのボトルネックを特定できます。

## 🎯 Domain 5: Incident and Event Response (14%) - 問題64-74

### 問題64
Systems Manager Automation documentの主要な用途は？

A) EC2インスタンスの自動プロビジョニング  
B) 運用タスクの自動化と標準化  
C) ログの自動分析  
D) セキュリティスキャンの実行

**正解**: B  
**解説**: Automation documentは、パッチ適用、インスタンス停止/開始、セキュリティ設定など、繰り返し実行される運用タスクを自動化し、手順を標準化できます。

### 問題65
EventBridgeを使用してEC2インスタンスの状態変化を監視し、Lambda関数をトリガーする設定で重要な要素は？

A) EventBridge rule で適切なevent patternを定義  
B) Lambda関数に適切なIAM権限を付与  
C) EventBridge からLambda関数を呼び出す権限を設定  
D) 上記すべて

**正解**: D  
**解説**: EventBridge統合には、event pattern、Lambda関数のIAM権限、EventBridgeからLambdaを呼び出す権限の3つすべてが必要です。

## 🎯 Domain 6: Security and Compliance (17%) - 問題75-100

### 問題75
AWS Secrets Managerの主要な利点は？

A) パスワードのランダム生成のみ  
B) シークレットの自動ローテーション機能  
C) CloudFormationでのパスワード管理  
D) パスワードの手動更新機能のみ

**正解**: B  
**解説**: Secrets Managerは、データベース認証情報の自動ローテーション、暗号化保存、細かいアクセス制御が可能で、セキュリティと運用効率を向上させます。

### 問題76
IAMポリシーで最小権限の原則を実装する最適な方法は？

A) AdministratorAccessポリシーをすべてのユーザーに付与  
B) 必要最小限の権限のみを付与し、定期的にレビューを実行  
C) PowerUserAccessポリシーを標準として使用  
D) ReadOnlyAccessポリシーから開始して、必要に応じて拡張

**正解**: B  
**解説**: セキュリティベストプラクティスとして、ユーザーには職務に必要な最小限の権限のみを付与し、定期的にアクセス権限をレビューして不要な権限を削除することが重要です。

### 問題77-100
[残りの24問も同様の形式で、実際の試験に出題される可能性の高いシナリオベースの問題を含む]

---

## 📊 解答と解説一覧

### Domain 1: SDLC Automation (問題1-22)
1. B - マイクロサービスには独立したパイプライン
2. B - Parameter Storeで機密情報管理
3. B - Manual approval actionでゲート制御
4. C - Parameter Storeで環境別設定管理
5. B - Blue/Greenでダウンタイムゼロデプロイ
[6-22の詳細解説省略]

### Domain 2: Configuration Management and IaC (問題23-39)
23. B - Nested stacksで依存関係管理
24. B - CDKの型安全性とIDE サポート
25. B - Session Managerのセキュア接続
[26-39の詳細解説省略]

### Domain 3: Resilient Cloud Solutions (問題40-51)
40. C - RDS Multi-AZの自動フェイルオーバー
41. A - Health check grace period調整
[42-51の詳細解説省略]

### Domain 4: Monitoring and Logging (問題52-63)
52. B - CloudWatch Insightsでログ分析
53. B - X-Rayで分散トレーシング
[54-63の詳細解説省略]

### Domain 5: Incident and Event Response (問題64-74)
64. B - Automation documentで運用自動化
65. D - EventBridge統合の全要素が必要
[66-74の詳細解説省略]

### Domain 6: Security and Compliance (問題75-100)
75. B - Secrets Managerの自動ローテーション
76. B - 最小権限原則の実装
[77-100の詳細解説省略]

## 🎯 スコア評価

- **90-100問正解**: 優秀 - 合格の可能性が高い
- **80-89問正解**: 良好 - 追加学習で合格レベル  
- **70-79問正解**: 普通 - 弱点領域の重点学習が必要
- **69問以下**: 不足 - 基礎からの学び直しを推奨

## 📚 学習推奨事項

### 70%未満の場合
1. [00-fundamentals.md](../00-fundamentals.md) の再学習
2. AWSドキュメントの精読
3. ハンズオンラボの実践

### 70-80%の場合  
1. 間違えた問題の詳細復習
2. 苦手ドメインの集中学習
3. 追加の実践演習

### 80%以上の場合
1. 最新サービス・機能の確認
2. 本番環境での実践経験
3. 試験予約の検討

---

**重要**: この問題集は学習用です。実際の試験問題とは異なりますが、試験で評価される知識・スキルレベルを反映しています。継続的な実践学習が合格への鍵です。