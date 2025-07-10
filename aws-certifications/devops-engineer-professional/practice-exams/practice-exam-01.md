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

### 問題6
CodeCommitリポジトリで開発チームが並行作業を効率的に管理するために、最適なブランチ戦略は？

A) すべての開発者がmasterブランチで直接作業する  
B) Git Flow戦略を使用して、feature/develop/master ブランチを分離する  
C) 開発者ごとに専用リポジトリを作成する  
D) ブランチを使用せず、タグのみで管理する

**正解**: B  
**解説**: Git Flow戦略は、feature、develop、masterブランチを分離することで、並行開発、機能統合、リリース管理を効率的に行えます。プルリクエストによるコードレビューも可能です。

### 問題7
CodeBuildで複数のプラットフォーム（Linux、Windows）向けにビルドを実行する最適な方法は？

A) 単一のbuildspec.ymlで条件分岐を使用する  
B) プラットフォームごとに別々のCodeBuildプロジェクトを作成する  
C) Docker Multi-stage buildを使用する  
D) Lambda関数でビルドプロセスを制御する

**正解**: B  
**解説**: プラットフォームごとに専用のCodeBuildプロジェクトを作成することで、各環境に最適化された設定、依存関係、ビルドスクリプトを使用できます。

### 問題8
CodePipelineでアーティファクトの暗号化を実装する際の設定は？

A) S3バケットのデフォルト暗号化のみ使用  
B) パイプライン作成時にKMS keyを指定してアーティファクトを暗号化  
C) CloudFormationテンプレートで暗号化設定  
D) 暗号化は自動で有効化されるため設定不要

**正解**: B  
**解説**: CodePipelineでは、パイプライン作成時にKMS keyを指定することで、アーティファクトの暗号化を有効化できます。これにより、機密情報を含むアーティファクトも安全に管理できます。

### 問題9
以下のCodeBuild buildspec.ymlファイルの設定で、環境変数を使用してビルドプロセスを制御する最適な方法は？

```yaml
version: 0.2
phases:
  pre_build:
    commands:
      - echo $AWS_DEFAULT_REGION
      - echo $ENVIRONMENT
```

A) buildspec.ymlファイルに直接環境変数を記述する  
B) CodeBuildプロジェクトの環境変数設定を使用し、Parameter Storeから動的に取得する  
C) Lambda関数で環境変数を設定する  
D) EC2インスタンスの環境変数を使用する

**正解**: B  
**解説**: CodeBuildプロジェクトの環境変数設定でParameter Storeから動的に取得することで、セキュリティを保ちながら環境に応じた設定を使用できます。

### 問題10
CodeCommitとCodeBuildを連携させて、プルリクエスト作成時に自動でビルドとテストを実行する設定方法は？

A) CloudWatch Eventsを使用してCodeCommitイベントを監視し、CodeBuildをトリガーする  
B) Lambda関数を使用してポーリングベースの監視を実装する  
C) CodeCommitのwebhook機能を使用する  
D) 手動でビルドを実行する

**正解**: A  
**解説**: CloudWatch Events（EventBridge）でCodeCommitのpull requestイベントを監視し、CodeBuildプロジェクトをトリガーすることで、自動的なビルドとテストを実現できます。

### 問題11
CodeDeployでAuto Scaling Groupにデプロイする際の設定で、インスタンスの健全性を確保する最適な方法は？

A) デプロイ前にAuto Scalingを停止する  
B) Blue/Green deploymentを使用し、新しいAuto Scaling Groupを作成する  
C) Rolling deploymentを使用し、一度に一定数のインスタンスのみを更新する  
D) 全インスタンスを同時に更新する

**正解**: C  
**解説**: Rolling deploymentを使用することで、一度に一定数のインスタンスのみを更新し、サービスの可用性を保ちながら段階的にデプロイできます。

### 問題12
CodePipelineでクロスリージョンデプロイメントを実装する際の考慮事項は？

A) 各リージョンで独立したパイプラインを作成する  
B) アーティファクトストアを各リージョンに配置し、リージョン間でアーティファクトを複製する  
C) 単一リージョンからすべてのリージョンにデプロイする  
D) リージョンごとに異なるAWSアカウントを使用する

**正解**: B  
**解説**: クロスリージョンデプロイメントでは、各リージョンにアーティファクトストアを配置し、CodePipelineがリージョン間でアーティファクトを自動的に複製します。

### 問題13
以下のCodeCommit操作で、大きなファイルを効率的に管理する方法は？

A) Git LFS（Large File Storage）を使用する  
B) ファイルを小さく分割して複数のコミットで管理する  
C) S3に保存してCodeCommitにはリンクのみを含める  
D) CodeCommitの制限に従って100MB以下のファイルのみを使用する

**正解**: A  
**解説**: Git LFSを使用することで、大きなファイルを効率的に管理できます。実際のファイルはS3に保存され、CodeCommitにはポインタのみが保存されます。

### 問題14
CodeBuildでDocker imageを使用してビルドを実行する際の最適な設定は？

A) AWS提供の標準イメージのみを使用する  
B) カスタムDockerイメージをECRにプッシュし、CodeBuildプロジェクトで指定する  
C) ローカルDockerイメージを使用する  
D) Docker Hubの公開イメージを直接使用する

**正解**: B  
**解説**: カスタムDockerイメージをECRにプッシュすることで、ビルド環境を完全に制御でき、依存関係やツールを事前に設定できます。

### 問題15
CodePipelineで障害発生時の自動復旧を実装する方法は？

A) CloudWatch Alarmを使用してパイプラインの失敗を監視し、Lambda関数で自動再実行する  
B) 手動でパイプラインを再実行する  
C) CodeCommitでロールバックを実行する  
D) 新しいパイプラインを作成する

**正解**: A  
**解説**: CloudWatch Alarmでパイプラインの状態を監視し、失敗時にLambda関数を実行してパイプラインを自動的に再実行できます。

### 問題16
CodeDeployで段階的デプロイメント（Canary deployment）を実装する際の設定は？

A) 一度に全インスタンスを更新する  
B) BlueGreenDeploymentCanaryを使用し、トラフィックを段階的に移行する  
C) Rolling deploymentのみを使用する  
D) 手動でトラフィックを制御する

**正解**: B  
**解説**: BlueGreenDeploymentCanaryを使用することで、新バージョンに段階的にトラフィックを移行し、問題があれば即座にロールバックできます。

### 問題17
CodeCommitで複数の開発者が同じファイルを変更した場合のコンフリクト解決の最適な方法は？

A) 最後にコミットした変更を優先する  
B) プルリクエストとコードレビューを使用してマージ前にコンフリクトを解決する  
C) 変更を破棄して最初からやり直す  
D) 自動的にマージツールを使用する

**正解**: B  
**解説**: プルリクエストとコードレビューを使用することで、コンフリクトを事前に検出し、開発者間でコラボレーションしながら適切に解決できます。

### 問題18
CodeBuildで複数のプログラミング言語を使用するプロジェクトのビルドを最適化する方法は？

A) 言語ごとに個別のbuildspec.ymlファイルを作成する  
B) 単一のbuildspec.ymlでphaseを分離し、必要な言語環境を動的に設定する  
C) 各言語用に個別のCodeBuildプロジェクトを作成する  
D) Lambda関数でビルドプロセスを制御する

**正解**: B  
**解説**: 単一のbuildspec.ymlでphaseを分離することで、複数の言語環境を効率的に管理でき、ビルドプロセスを統一できます。

### 問題19
CodePipelineでサードパーティツール（Jenkins、GitLab CI）との統合を実装する方法は？

A) カスタムアクションを作成してAPIを通じて統合する  
B) CodePipelineのみを使用してサードパーティツールを置き換える  
C) Lambda関数でサードパーティツールを呼び出す  
D) 手動でサードパーティツールを実行する

**正解**: A  
**解説**: CodePipelineのカスタムアクション機能を使用して、サードパーティツールのAPIを呼び出し、統合されたパイプラインを構築できます。

### 問題20
CodeCommitで大規模チームの権限管理を効率的に実装する方法は？

A) 全開発者にフルアクセス権限を付与する  
B) IAMポリシーとリソースベースポリシーを組み合わせて、チームとリポジトリごとに細かく権限を設定する  
C) 単一のIAMグループですべての権限を管理する  
D) CodeCommitの権限設定を使用しない

**正解**: B  
**解説**: IAMポリシーとリソースベースポリシーを組み合わせることで、チーム構造に応じた細かい権限設定が可能になり、セキュリティと効率性を両立できます。

### 問題21
以下のCodeBuild環境で、ビルドパフォーマンスを向上させる最適な設定は？

A) 最小のcompute typeを使用してコストを削減する  
B) キャッシュを有効にし、依存関係とビルドアーティファクトをS3に保存する  
C) 毎回クリーンな環境でビルドを実行する  
D) ローカルキャッシュのみを使用する

**正解**: B  
**解説**: S3キャッシュを有効にすることで、依存関係のダウンロードとビルドアーティファクトの再利用が可能になり、ビルド時間を大幅に短縮できます。

### 問題22
CodeDeployでLambda関数のデプロイを実装する際の設定は？

A) EC2インスタンスと同じ設定を使用する  
B) Lambda関数の別名（Alias）とバージョニングを使用して段階的デプロイを実装する  
C) 直接Lambda関数を更新する  
D) CodeDeployはLambda関数に対応していない

**正解**: B  
**解説**: Lambda関数のデプロイでは、別名（Alias）とバージョニングを使用することで、段階的なトラフィック移行とロールバックが可能になります。

## 🎯 Domain 2: Configuration Management and IaC (19%) - 問題23-41

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

### 問題26
以下のCloudFormationテンプレートで、Parameter Storeから値を取得する動的参照の正しい構文は？

```yaml
Resources:
  MyInstance:
    Type: AWS::EC2::Instance
    Properties:
      ImageId: ami-12345678
      InstanceType: t3.micro
      UserData:
        Fn::Base64: !Sub |
          #!/bin/bash
          DB_PASSWORD=?
```

A) `${ssm:parameter-name}`  
B) `{{resolve:ssm:parameter-name}}`  
C) `!GetAtt ParameterStore.Value`  
D) `{Ref: ParameterStore}`

**正解**: B  
**解説**: CloudFormationでは、`{{resolve:ssm:parameter-name}}`構文を使用してParameter Storeから動的に値を取得できます。セキュアストリングの場合は`{{resolve:ssm-secure:parameter-name}}`を使用します。

### 問題27
CloudFormationで既存のAWSリソースをスタック管理に組み込む方法は？

A) 既存リソースを削除して再作成する  
B) Import resources機能を使用する  
C) CloudFormationでは既存リソースを管理できない  
D) 手動でリソースIDを指定する

**正解**: B  
**解説**: CloudFormationのImport resources機能を使用して、既存のAWSリソースを既存のスタックに組み込むことができます。リソースの物理IDとテンプレートを指定する必要があります。

### 問題28
AWS CDKで環境（dev、staging、prod）ごとに異なる設定を管理する最適な方法は？

A) 環境ごとに異なるCDKアプリケーションを作成する  
B) Context valuesとEnvironment-specific stacksを使用する  
C) ハードコードされた値を使用する  
D) 手動で設定を変更する

**正解**: B  
**解説**: CDKでは、cdk.jsonのcontextや環境変数を使用して環境固有の設定を管理し、環境ごとに異なるスタックを作成できます。

### 問題29
Systems Manager Patch Managerで大規模なEC2環境のパッチ管理を自動化する設定は？

A) 各インスタンスで個別にパッチを適用する  
B) Maintenance WindowとPatch Groupを使用して、スケジュールされたパッチ適用を実装する  
C) 手動でパッチを適用する  
D) Auto Scalingグループでインスタンスを置き換える

**正解**: B  
**解説**: Maintenance WindowとPatch Groupを組み合わせることで、大規模環境でのパッチ適用を自動化できます。異なるグループに異なるスケジュールを設定可能です。

### 問題30
以下のTerraformコードで、AWSプロバイダーのバージョンを固定する最適な方法は？

```hcl
terraform {
  required_providers {
    aws = {
      source = "hashicorp/aws"
      version = ?
    }
  }
}
```

A) `version = "latest"`  
B) `version = "~> 4.0"`  
C) バージョン指定なし  
D) `version = "*"`

**正解**: B  
**解説**: `~> 4.0`を使用することで、メジャーバージョンを固定しながらマイナーバージョンとパッチバージョンの更新を許可できます。これにより、互換性を保ちながら改善も取り込めます。

### 問題31
CloudFormationドリフト検出機能の主要な用途は？

A) スタックの作成時間を短縮する  
B) 手動変更により実際のリソースとテンプレートの差異を検出する  
C) スタックの削除を自動化する  
D) テンプレートの検証を行う

**正解**: B  
**解説**: ドリフト検出機能は、CloudFormationで管理されているリソースが手動で変更された場合、テンプレートと実際のリソース状態の差異を検出できます。

### 問題32
Systems Manager Documents (SSM Documents)で複数のEC2インスタンスに対して設定変更を実行する方法は？

A) 各インスタンスでSSHログインして手動実行  
B) Run Commandを使用してDocumentを実行する  
C) Lambda関数から各インスタンスに個別にアクセス  
D) CloudFormationテンプレートを使用

**正解**: B  
**解説**: Systems Manager Run Commandを使用することで、DocumentをタグやInstanceIDで指定した複数のインスタンスに対して同時に実行できます。

### 問題33
AWS CDKで複数のAWSアカウントとリージョンにデプロイする際の設定方法は？

A) 各アカウントで個別のCDKアプリケーションを作成する  
B) Environment（account、region）を指定してクロスアカウントデプロイを実装する  
C) 手動でリソースを各アカウントに複製する  
D) CloudFormationテンプレートにエクスポートして個別実行

**正解**: B  
**解説**: CDKでは、Stack作成時にEnvironmentを指定することで、複数のAWSアカウントとリージョンにデプロイできます。適切なIAM権限の設定も必要です。

### 問題34
以下のCloudFormationテンプレートで、条件文を使用してリソースを条件的に作成する構文は？

```yaml
Parameters:
  CreateDatabase:
    Type: String
    Default: "false"
    AllowedValues: ["true", "false"]

Conditions:
  ShouldCreateDB: !Equals [!Ref CreateDatabase, "true"]

Resources:
  Database:
    Type: AWS::RDS::DBInstance
    Condition: ?
```

A) `!If [ShouldCreateDB, true, false]`  
B) `ShouldCreateDB`  
C) `!Condition ShouldCreateDB`  
D) `!Equals [CreateDatabase, "true"]`

**正解**: B  
**解説**: CloudFormationでは、Conditionセクションで定義した条件名を直接リソースのCondition属性に指定します。

### 問題35
Systems Manager Parameter Store Hierarchyを使用して、アプリケーション設定を階層的に管理する利点は？

A) ストレージコストの削減  
B) 設定の階層化により、環境やアプリケーションごとの設定管理が容易になる  
C) 高速なパラメータ取得  
D) 自動的なパラメータ検証

**正解**: B  
**解説**: Parameter Store Hierarchyを使用することで、`/myapp/prod/db/password`のような階層構造で設定を管理でき、環境やアプリケーションごとの設定を効率的に管理できます。

### 問題36
Terraformで状態ファイル（tfstate）を複数人で安全に共有する方法は？

A) ローカルファイルシステムで共有する  
B) S3バケットをリモートバックエンドとして使用し、DynamoDBでロックを管理する  
C) GitHubリポジトリで状態ファイルを管理する  
D) 手動で状態ファイルを同期する

**正解**: B  
**解説**: S3をリモートバックエンドとして使用し、DynamoDBでロックを管理することで、複数人での協業時の状態ファイル管理を安全に行えます。

### 問題37
CloudFormationで大きなテンプレートファイルの管理とデプロイを効率化する方法は？

A) 単一ファイルにすべてを含める  
B) Nested stacksとPackaging（aws cloudformation package）を使用する  
C) 手動でリソースを作成する  
D) 複数のAWSアカウントに分散する

**正解**: B  
**解説**: Nested stacksで論理的な分割を行い、aws cloudformation packageコマンドでテンプレートとアーティファクトをS3にパッケージングすることで、効率的な管理とデプロイが可能になります。

### 問題38
AWS Config Rulesと Systems Manager Compliance を組み合わせて、インフラストラクチャコンプライアンスを自動化する方法は？

A) 手動でコンプライアンスチェックを実行する  
B) Config Rulesでリソースの設定を評価し、Systems Manager Complianceでパッチ適用状況を監視する  
C) CloudTrailでのみ監視する  
D) 外部ツールを使用する

**正解**: B  
**解説**: Config Rulesでリソースの設定コンプライアンスを評価し、Systems Manager Complianceでパッチ適用状況を監視することで、包括的なコンプライアンス管理が可能になります。

### 問題39
CDKで既存のCloudFormationテンプレートを段階的に移行する方法は？

A) 全てのリソースを一度に移行する  
B) CloudFormation Includeを使用して既存テンプレートを取り込み、段階的にCDKコードに移行する  
C) 移行は不可能  
D) 手動でリソースを再作成する

**正解**: B  
**解説**: CDKのCloudFormation Include機能を使用して、既存のCloudFormationテンプレートを取り込み、段階的にCDKコードに移行できます。

### 問題40
Systems Manager Inventory を使用して、EC2インスタンスの構成情報を収集する利点は？

A) インスタンスの作成時間短縮  
B) インストールされているソフトウェア、設定、パッチレベルの可視化  
C) インスタンスの自動停止  
D) ネットワークパフォーマンスの向上

**正解**: B  
**解説**: Systems Manager Inventoryは、EC2インスタンスのソフトウェア、設定、パッチレベルなどの情報を収集し、コンプライアンスとセキュリティの監視に使用できます。

### 問題41
以下のTerraformコードで、モジュールを使用してリソースを再利用可能にする構文は？

```hcl
module "vpc" {
  source = "./modules/vpc"
  
  cidr_block = "10.0.0.0/16"
  availability_zones = ["us-east-1a", "us-east-1b"]
  
  ?
}
```

A) `version = "1.0"`  
B) `depends_on = [aws_vpc.main]`  
C) `tags = var.common_tags`  
D) すべて正しい

**正解**: D  
**解説**: Terraformモジュールでは、version指定、depends_on、変数の受け渡しなどがすべて有効な構文です。これにより、再利用可能で保守性の高いインフラストラクチャコードを作成できます。

## 🎯 Domain 3: Monitoring and Logging (15%) - 問題42-56

### 問題42
CloudWatch Logsで大量のログデータを効率的に分析する方法は？

A) 手動でログファイルをダウンロードして分析  
B) CloudWatch Insights を使用したクエリベース分析  
C) S3にエクスポートしてExcelで分析  
D) CloudTrailと連携して分析

**正解**: B  
**解説**: CloudWatch Insightsは、SQLライクなクエリ言語を使用して、CloudWatch Logsのデータを効率的に検索、分析、可視化できます。

### 問題43
X-Rayを使用した分散トレーシングの主要な目的は？

A) アプリケーションのセキュリティ向上  
B) マイクロサービス間のリクエストフローとパフォーマンスの可視化  
C) ログの集中管理  
D) アプリケーションの自動復旧

**正解**: B  
**解説**: X-Rayは、分散システムでのリクエストの流れ、各コンポーネントでの実行時間、エラーの発生箇所を可視化し、パフォーマンスのボトルネックを特定できます。

### 問題44
以下のCloudWatch Logsの設定で、アプリケーションログを構造化して効率的に検索する方法は？

```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "level": "ERROR",
  "message": "Database connection failed",
  "service": "user-service",
  "trace_id": "abc123"
}
```

A) プレーンテキスト形式でログを出力する  
B) JSON形式でログを出力し、CloudWatch Logsフィルターパターンを使用する  
C) バイナリ形式でログを保存する  
D) 手動でログをパースする

**正解**: B  
**解説**: JSON形式でログを出力することで、CloudWatch Logsのフィルターパターンやクエリ機能を使用して、特定のフィールドで効率的に検索できます。

### 問題45
CloudWatch Dashboardで複数のAWSアカウントとリージョンのメトリクスを統合して表示する方法は？

A) 各アカウントで個別のダッシュボードを作成する  
B) Cross-account role assumptionとクロスリージョンメトリクスを使用する  
C) 手動でメトリクスをコピーする  
D) 単一アカウントのメトリクスのみを表示する

**正解**: B  
**解説**: CloudWatch Dashboardでは、IAMロールを使用してクロスアカウントアクセスを設定し、複数のリージョンのメトリクスを統合して表示できます。

### 問題46
AWS X-Ray で Lambda関数のパフォーマンスを詳細に分析する設定は？

A) Lambda関数でX-Ray SDKを使用せず、基本的なトレースのみを有効にする  
B) X-Ray トレースを有効にし、Lambda関数内でX-Ray SDKを使用してカスタムセグメントを作成する  
C) CloudWatch Logsのみを使用する  
D) 手動でパフォーマンスを測定する

**正解**: B  
**解説**: X-Ray SDKを使用することで、Lambda関数内の特定の処理をセグメント化し、外部API呼び出しやデータベースアクセスなどの詳細なパフォーマンス分析が可能になります。

### 問題47
CloudWatch Alarmで複数のメトリクスを組み合わせて複合的な監視を実装する方法は？

A) 各メトリクスで個別のアラームを作成する  
B) Composite Alarmを使用して複数のアラームを論理的に結合する  
C) 手動でメトリクスを監視する  
D) 単一のメトリクスのみを監視する

**正解**: B  
**解説**: Composite Alarmを使用することで、複数のアラームをAND/OR条件で組み合わせ、より柔軟で複合的な監視が可能になります。

### 問題48
以下のCloudWatch Logsの設定で、ログの保存コストを最適化する方法は？

A) すべてのログを永続的に保存する  
B) Log Retention Policyを設定し、古いログを自動削除する  
C) 手動でログを削除する  
D) ログ出力を停止する

**正解**: B  
**解説**: Log Retention Policyを設定することで、不要になった古いログを自動的に削除し、ストレージコストを削減できます。

### 問題49
CloudWatch Synthetics を使用して、Webアプリケーションの可用性を継続的に監視する設定は？

A) 手動でWebサイトの動作を定期的に確認する  
B) Canary scriptsを作成して、スケジュールされた自動監視を実装する  
C) CloudWatch Dashboardのみを使用する  
D) 外部の監視サービスを使用する

**正解**: B  
**解説**: CloudWatch Syntheticsでは、Canary scriptsを使用してWebアプリケーションの機能を自動的にテストし、可用性とパフォーマンスを継続的に監視できます。

### 問題50
CloudWatch Eventsを使用して、EC2インスタンスの状態変化を監視し、自動的にアクションを実行する設定は？

A) 手動でインスタンスの状態を確認する  
B) Event PatternでEC2状態変化イベントを捕捉し、Lambda関数やSNSなどのターゲットアクションを設定する  
C) CloudWatch Dashboardで監視する  
D) 定期的にAPIを呼び出してチェックする

**正解**: B  
**解説**: CloudWatch Events（EventBridge）のEvent Patternを使用して、EC2インスタンスの状態変化を自動的に検知し、Lambda関数やSNSなどのターゲットアクションを実行できます。

### 問題51
以下のCloudWatch Logsの設定で、機密情報を含むログを安全に管理する方法は？

A) プレーンテキストでログを保存する  
B) Log Group暗号化を有効にし、IAMポリシーでアクセスを制限する  
C) 機密情報をログに含めない  
D) 手動でログを暗号化する

**正解**: B  
**解説**: CloudWatch Logsでは、KMS暗号化を有効にして保存時の暗号化を実現し、IAMポリシーで細かいアクセス制御を実装できます。ただし、機密情報の除外も重要です。

### 問題52
CloudWatch Container Insightsで、EKSクラスターのパフォーマンスを詳細に監視する設定は？

A) 標準のCloudWatch Agentのみを使用する  
B) Container Insightsを有効にし、CloudWatch Agentをサイドカーとして展開する  
C) 手動でメトリクスを収集する  
D) 外部の監視ツールを使用する

**正解**: B  
**解説**: Container Insightsを有効にすることで、EKSクラスターのCPU、メモリ、ネットワーク、ストレージメトリクスを詳細に監視できます。

### 問題53
CloudWatch Logsの設定で、アプリケーションログを効率的にS3にエクスポートする方法は？

A) 手動でログファイルをダウンロードしてS3にアップロード  
B) CloudWatch Logsのエクスポート機能を使用して、スケジュールされた自動エクスポートを設定する  
C) Lambda関数で個別にログを処理する  
D) 外部ツールを使用する

**正解**: B  
**解説**: CloudWatch Logsのエクスポート機能を使用することで、ログデータを効率的にS3にエクスポートし、長期保存や分析に使用できます。

### 問題54
AWS X-Ray で分散システムのエラー分析を効率的に実行する方法は？

A) 手動でログファイルを確認する  
B) X-Ray Service Mapでエラーの発生箇所を特定し、Trace詳細でエラーの原因を分析する  
C) CloudWatch Logsのみを使用する  
D) 外部の分析ツールを使用する

**正解**: B  
**解説**: X-Ray Service Mapでシステム全体のエラー発生箇所を視覚的に特定し、個別のTraceを詳細に分析することで、エラーの根本原因を効率的に特定できます。

### 問題55
CloudWatch Anomaly Detectionを使用して、異常なメトリクスパターンを自動検出する設定は？

A) 手動でメトリクスの異常を監視する  
B) 機械学習ベースのAnomaly Detectionを有効にし、自動的に異常を検出してアラートを生成する  
C) 静的な閾値のみを使用する  
D) 外部の異常検出ツールを使用する

**正解**: B  
**解説**: CloudWatch Anomaly Detectionは、機械学習を使用してメトリクスの正常なパターンを学習し、異常を自動的に検出してアラートを生成できます。

### 問題56
以下のCloudWatch Insightsクエリで、エラーログの頻度を分析する正しい構文は？

A) `SELECT COUNT(*) FROM logs WHERE level = "ERROR"`  
B) `fields @timestamp, @message | filter @message like /ERROR/ | stats count(*) by bin(5m)`  
C) `ERROR * | count`  
D) `grep ERROR | wc -l`

**正解**: B  
**解説**: CloudWatch Insightsでは、`fields`、`filter`、`stats`構文を使用して、時間帯別のエラーログ頻度を分析できます。`bin(5m)`で5分間隔でグループ化できます。

## 🎯 Domain 4: Policies and Standards Automation (10%) - 問題57-66

### 問題57
AWS Config Rules を使用して、組織全体のコンプライアンス標準を自動的に監視する最適な方法は？

A) 手動でリソースの設定を確認する  
B) Organizational Config Rules を設定し、すべてのアカウントで一元的にコンプライアンスを監視する  
C) 各アカウントで個別にConfig Rulesを設定する  
D) 外部のコンプライアンスツールを使用する

**正解**: B  
**解説**: AWS Organizations と Config Rules を組み合わせることで、組織全体でコンプライアンス標準を一元的に定義・監視できます。

### 問題58
Service Control Policies (SCPs) を使用して、開発環境での特定のAWSサービスの使用を制限する設定は？

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Deny",
      "Action": [
        "ec2:TerminateInstances"
      ],
      "Resource": "*",
      "Condition": {
        "StringEquals": {
          "aws:RequestedRegion": "us-east-1"
        }
      }
    }
  ]
}
```

A) Allow効果を使用する  
B) Deny効果を使用し、条件を指定して特定の環境での操作を制限する  
C) IAMポリシーのみを使用する  
D) リソースベースポリシーを使用する

**正解**: B  
**解説**: SCPsでは、Deny効果を使用して組織レベルでの制限を設定できます。条件を使用することで、特定のリージョンや環境での操作を制限できます。

### 問題59
AWS Systems Manager Compliance を使用して、パッチ適用のコンプライアンス状況を自動監視する方法は？

A) 手動でパッチ適用状況を確認する  
B) Patch Compliance rules を設定し、自動的にコンプライアンス状況を評価する  
C) 外部ツールでパッチ管理を行う  
D) CloudWatch Alarmのみを使用する

**正解**: B  
**解説**: Systems Manager Compliance では、パッチ適用状況を自動的に評価し、コンプライアンス違反を検出できます。

### 問題60
AWS Security Hub を使用して、複数のセキュリティサービスの発見事項を統合管理する設定は？

A) 各セキュリティサービスで個別に管理する  
B) Security Standards を有効にし、GuardDuty、Inspector、Configなどの発見事項を統合表示する  
C) 手動でセキュリティ状況を確認する  
D) 外部のSIEMツールのみを使用する

**正解**: B  
**解説**: Security Hub は、複数のAWSセキュリティサービスからの発見事項を統合し、統一されたダッシュボードで管理できます。

### 問題61
以下のAWS Config Rule で、未使用のセキュリティグループを検出する設定は？

A) `ec2-security-group-attached-to-eni`  
B) `unused-security-groups`  
C) `ec2-security-group-attached-to-eni` ルールを使用し、ENIに関連付けられていないセキュリティグループを検出  
D) 手動でセキュリティグループを確認

**正解**: C  
**解説**: `ec2-security-group-attached-to-eni` Config Rule を使用することで、ENI（Elastic Network Interface）に関連付けられていない未使用のセキュリティグループを自動的に検出できます。

### 問題62
AWS Control Tower を使用して、新しいAWSアカウントにガバナンスポリシーを自動適用する方法は？

A) 手動で各アカウントにポリシーを設定する  
B) Guardrails を設定し、Account Factory でプロビジョニングされる新しいアカウントに自動適用する  
C) 外部ツールを使用する  
D) CloudFormation StackSets のみを使用する

**正解**: B  
**解説**: Control Tower の Guardrails 機能により、Account Factory で作成される新しいアカウントに自動的にガバナンスポリシーを適用できます。

### 問題63
AWS CloudFormation Guard を使用して、インフラストラクチャテンプレートのポリシー準拠を事前検証する方法は？

A) デプロイ後に手動で確認する  
B) Guard rules を定義し、CI/CDパイプラインでテンプレートを事前検証する  
C) CloudFormation テンプレートの手動レビューのみを実行する  
D) 外部の検証ツールを使用する

**正解**: B  
**解説**: CloudFormation Guard では、ポリシールールを定義してテンプレートを事前検証でき、CI/CDパイプラインに組み込むことで継続的なコンプライアンス確保が可能です。

### 問題64
AWS IAM Access Analyzer を使用して、外部エンティティへの意図しないアクセス権限を検出する設定は？

A) 手動でIAMポリシーを確認する  
B) Access Analyzer を有効にし、外部プリンシパルへのアクセス権限を自動検出する  
C) CloudTrail ログのみを確認する  
D) 外部ツールを使用する

**正解**: B  
**解説**: IAM Access Analyzer は、S3バケット、IAMロール、KMSキーなどのリソースが外部エンティティからアクセス可能かを自動的に分析し、意図しない公開を検出できます。

### 問題65
AWS Organizations Service Control Policies (SCPs) で、特定のIAMアクションを組織全体で制限する際の最適な戦略は？

A) 各アカウントのIAMポリシーのみで制限する  
B) 段階的なアプローチを使用し、まずテスト環境で検証してから本番環境に適用する  
C) 一度にすべてのアカウントに適用する  
D) SCPを使用しない

**正解**: B  
**解説**: SCPは組織全体に影響を与えるため、段階的なアプローチでまずテスト環境で検証し、影響を確認してから本番環境に適用することが重要です。

### 問題66
AWS CloudFormation Drift Detection を使用して、インフラストラクチャの設定ドリフトを継続的に監視する自動化設定は？

A) 手動でドリフト検出を実行する  
B) CloudWatch Events と Lambda を使用して、定期的にドリフト検出を実行し、結果をSNSで通知する  
C) 外部ツールでドリフトを監視する  
D) ドリフト検出は実行しない

**正解**: B  
**解説**: CloudWatch Events（EventBridge）でスケジュール実行し、Lambda関数でドリフト検出を実行、結果をSNSで通知することで、継続的な監視を自動化できます。

## 🎯 Domain 5: Incident and Event Response (18%) - 問題67-84

### 問題67
Systems Manager Automation documentの主要な用途は？

A) EC2インスタンスの自動プロビジョニング  
B) 運用タスクの自動化と標準化  
C) ログの自動分析  
D) セキュリティスキャンの実行

**正解**: B  
**解説**: Automation documentは、パッチ適用、インスタンス停止/開始、セキュリティ設定など、繰り返し実行される運用タスクを自動化し、手順を標準化できます。

### 問題68
EventBridgeを使用してEC2インスタンスの状態変化を監視し、Lambda関数をトリガーする設定で重要な要素は？

A) EventBridge rule で適切なevent patternを定義  
B) Lambda関数に適切なIAM権限を付与  
C) EventBridge からLambda関数を呼び出す権限を設定  
D) 上記すべて

**正解**: D  
**解説**: EventBridge統合には、event pattern、Lambda関数のIAM権限、EventBridgeからLambdaを呼び出す権限の3つすべてが必要です。

### 問題69
以下のCloudWatch Alarmで、EC2インスタンスの異常を検出して自動復旧を実装する設定は？

```json
{
  "AlarmName": "EC2-StatusCheck-Failed",
  "MetricName": "StatusCheckFailed_System",
  "Namespace": "AWS/EC2",
  "Statistic": "Maximum",
  "Period": 60,
  "EvaluationPeriods": 2,
  "Threshold": 0,
  "ComparisonOperator": "GreaterThanThreshold",
  "AlarmActions": ["?"]
}
```

A) SNS notification のみ  
B) `arn:aws:automate:region:ec2:recover` アクションを使用して自動復旧  
C) Lambda関数の手動実行  
D) 手動でインスタンスを復旧

**正解**: B  
**解説**: EC2の自動復旧アクション `arn:aws:automate:region:ec2:recover` を AlarmActions に設定することで、システムステータスチェック失敗時に自動復旧を実行できます。

### 問題70
AWS Systems Manager Session Manager を使用して、インシデント時のトラブルシューティングアクセスを安全に実装する方法は？

A) SSH鍵を使用した従来のSSHアクセス  
B) Session Manager でIAM権限ベースのアクセスを実装し、セッションログを記録する  
C) RDPアクセスを使用する  
D) 物理的なサーバーアクセス

**正解**: B  
**解説**: Session Manager を使用することで、SSH鍵なしでIAM権限ベースの安全なアクセスが可能になり、すべてのセッションがCloudTrailに記録されます。

### 問題71
Amazon SNS と Amazon SQS を組み合わせて、インシデント通知の信頼性を向上させる設定は？

A) SNSのみを使用する  
B) SNS トピックからSQS キューに配信し、Dead Letter Queue を設定してメッセージ配信の信頼性を確保する  
C) SQSのみを使用する  
D) メール通知のみを使用する

**正解**: B  
**解説**: SNSからSQSへの配信にDead Letter Queueを設定することで、配信失敗したメッセージを保存し、通知の信頼性を向上させることができます。

### 問題72
AWS Lambda と Amazon DynamoDB を使用して、インシデント対応の状況を追跡するシステムを構築する際の最適なアーキテクチャは？

A) Lambda関数から直接DynamoDBにアクセスする  
B) EventBridge、Lambda、DynamoDB Streams を組み合わせて、イベント駆動型の状況追跡システムを構築する  
C) 手動でデータベースを更新する  
D) CloudWatch Logsのみを使用する

**正解**: B  
**解説**: EventBridgeでイベントを受信し、Lambda関数で処理してDynamoDBに保存、DynamoDB Streamsで変更を追跡することで、リアルタイムなインシデント追跡が可能になります。

### 問題73
AWS Step Functions を使用して、複雑なインシデント対応ワークフローを自動化する利点は？

A) 単純なタスクの実行のみ可能  
B) 複数のAWSサービスを組み合わせた複雑なワークフローを視覚的に定義し、エラーハンドリングと再試行を実装できる  
C) 手動での実行が必要  
D) 単一のLambda関数のみで完結

**正解**: B  
**解説**: Step Functions では、複数のサービスを組み合わせた複雑なワークフローを状態機械として定義し、エラーハンドリング、再試行、分岐処理を実装できます。

### 問題74
AWS Personal Health Dashboard を使用して、組織レベルでのAWSサービス問題を監視する設定は？

A) 個人アカウントのHealth Dashboardのみを使用する  
B) AWS Health API を使用して組織レベルのヘルス情報を取得し、カスタムダッシュボードを構築する  
C) 手動でAWSサービス状況を確認する  
D) 外部の監視サービスのみを使用する

**正解**: B  
**解説**: AWS Health API を使用することで、組織レベルでのAWSサービス問題を programmatically に監視し、カスタムダッシュボードや通知システムを構築できます。

### 問題75
CloudWatch Events（EventBridge）を使用して、Auto Scaling のスケールアウトイベントを監視し、自動的にログ収集を強化する設定は？

A) 手動でログレベルを変更する  
B) Auto Scaling イベントを捕捉し、Lambda関数でアプリケーションのログレベルを動的に調整する  
C) 静的なログ設定のみを使用する  
D) ログ収集を停止する

**正解**: B  
**解説**: EventBridge でAuto Scalingイベントを監視し、Lambda関数でアプリケーションの設定を動的に変更することで、スケールアウト時のトラブルシューティングを支援できます。

### 問題76
AWS X-Ray と CloudWatch を統合して、分散システムでのインシデント根本原因分析を効率化する方法は？

A) X-Rayのみを使用する  
B) X-Ray トレースデータとCloudWatch メトリクスを関連付けて、パフォーマンス問題の根本原因を特定する  
C) CloudWatch Logsのみを使用する  
D) 手動でログを分析する

**正解**: B  
**解説**: X-Rayのトレースデータから関連するCloudWatchメトリクスにドリルダウンできるため、分散システムでのパフォーマンス問題を効率的に特定できます。

### 問題77
AWS Systems Manager Run Command を使用して、インシデント時に複数のEC2インスタンスで同時に診断コマンドを実行する方法は？

A) 各インスタンスにSSHでログインして手動実行  
B) Run Command でタグベースのターゲット選択を使用し、並列で診断コマンドを実行する  
C) 順次一つずつインスタンスで実行する  
D) 外部ツールを使用する

**正解**: B  
**解説**: Run Command では、タグやinstance IDでターゲットを指定し、複数のインスタンスで並列にコマンドを実行できるため、迅速な診断が可能です。

### 問題78
Amazon CloudWatch Container Insights を使用して、EKSクラスターでのインシデント対応を支援する設定は？

A) 基本的なCloudWatch メトリクスのみを使用する  
B) Container Insights を有効にして、ポッド、ノード、サービスレベルの詳細メトリクスとログを統合監視する  
C) 手動でコンテナログを確認する  
D) 外部の監視ツールのみを使用する

**正解**: B  
**解説**: Container Insights では、EKSクラスター全体の詳細なメトリクスとログを統合して監視でき、Kubernetesレベルでのインシデント対応を効率化できます。

### 問題79
AWS Config を使用して、インシデント時のリソース設定変更履歴を追跡する設定は？

A) 手動で設定変更を記録する  
B) Config を有効にして、リソースの設定変更履歴を自動記録し、特定時点での設定を確認できるようにする  
C) CloudTrail のみを使用する  
D) 外部ツールで変更を追跡する

**正解**: B  
**解説**: AWS Config では、リソースの設定変更を自動的に記録し、特定時点での設定状況を確認できるため、インシデント時の原因調査に有効です。

### 問題80
以下のEventBridge rule で、RDSデータベースの障害イベントを監視する設定は？

```json
{
  "source": ["aws.rds"],
  "detail-type": ["RDS DB Instance Event"],
  "detail": {
    "EventCategories": ["?"]
  }
}
```

A) `["backup"]`  
B) `["failure", "failover", "notification"]`  
C) `["maintenance"]`  
D) `["configuration change"]`

**正解**: B  
**解説**: RDSの障害関連イベントを監視するには、failure、failover、notification カテゴリを指定します。これにより、データベース障害時の自動対応が可能になります。

### 問題81
AWS Lambda と Amazon Kinesis を使用して、リアルタイムログ分析によるインシデント検出システムを構築する方法は？

A) バッチ処理でログを分析する  
B) Kinesis Data Streams でログをストリーミングし、Lambda関数でリアルタイム分析してアラートを生成する  
C) 手動でログを確認する  
D) 定期的なログダウンロードで分析する

**正解**: B  
**解説**: Kinesis Data Streams でログデータをリアルタイムでストリーミングし、Lambda関数で即座に分析することで、迅速なインシデント検出が可能になります。

### 問題82
AWS Systems Manager Maintenance Windows を使用して、定期的なシステムメンテナンスを自動化する設定は？

A) 手動でメンテナンスを実行する  
B) Maintenance Window を設定し、指定された時間にAutomation documentsやRun Commandsを自動実行する  
C) 外部のスケジューラーを使用する  
D) 24時間365日稼働させる

**正解**: B  
**解説**: Maintenance Windows を使用することで、指定された時間枠でのメンテナンス作業を自動化でき、システムの安定性向上に貢献できます。

### 問題83
Amazon GuardDuty の脅威検出結果を EventBridge と Lambda を使用して自動対応システムに統合する方法は？

A) 手動で脅威に対応する  
B) GuardDuty の findings を EventBridge で受信し、Lambda関数で自動的にセキュリティグループ更新やインスタンス隔離を実行する  
C) 外部のセキュリティツールのみを使用する  
D) GuardDuty の結果を確認するだけ

**正解**: B  
**解説**: GuardDuty の脅威検出結果を EventBridge で受信し、Lambda関数で自動的に対応アクション（ネットワーク隔離、インスタンス停止など）を実行できます。

### 問題84
AWS Support API を使用して、インシデント管理プロセスにAWSサポートケースの情報を統合する方法は？

A) 手動でサポートケースを管理する  
B) Support API を使用してサポートケースの作成、更新、追跡を自動化し、社内のインシデント管理システムと統合する  
C) メールでのやり取りのみ  
D) 外部のサポートシステムのみを使用する

**正解**: B  
**解説**: Support API を使用することで、AWSサポートケースの programmatic な管理が可能になり、社内のインシデント管理プロセスと統合できます。

## 🎯 Domain 6: High Availability, Fault Tolerance, and Disaster Recovery (16%) - 問題85-100

### 問題85
マルチAZ構成のRDSインスタンスで自動フェイルオーバーが発生する条件は？

A) CPU使用率が90%を超えた場合  
B) プライマリインスタンスの計画メンテナンス  
C) プライマリインスタンスの障害またはAZ障害  
D) ディスク容量が不足した場合

**正解**: C  
**解説**: マルチAZ RDSは、プライマリインスタンスまたはAZ レベルの障害時に自動的にスタンバイインスタンスにフェイルオーバーします。計画メンテナンス時は事前にフェイルオーバーが実行されます。

### 問題86
Auto Scalingグループで、新しくプロビジョニングされたインスタンスがロードバランサーのヘルスチェックに失敗し続ける場合の対処法は？

A) Health check grace periodを延長する  
B) インスタンスタイプを変更する  
C) Auto Scalingを無効にする  
D) ヘルスチェックを無効にする

**正解**: A  
**解説**: Health check grace periodを適切に設定することで、アプリケーションの起動に十分な時間を与えることができます。デフォルトは300秒ですが、アプリケーションの起動時間に応じて調整が必要です。

### 問題87
以下のApplication Load Balancer設定で、複数のAZにわたる高可用性を実現する構成は？

```json
{
  "LoadBalancerArn": "arn:aws:elasticloadbalancing:...",
  "Subnets": ["subnet-1a", "subnet-1b", "subnet-1c"],
  "AvailabilityZones": ["us-east-1a", "us-east-1b", "us-east-1c"],
  "HealthCheck": {
    "Path": "/health",
    "IntervalSeconds": 30,
    "TimeoutSeconds": 5,
    "HealthyThresholdCount": 2,
    "UnhealthyThresholdCount": "?"
  }
}
```

A) `UnhealthyThresholdCount: 1`  
B) `UnhealthyThresholdCount: 3`  
C) `UnhealthyThresholdCount: 5`  
D) `UnhealthyThresholdCount: 10`

**正解**: B  
**解説**: UnhealthyThresholdCountを3に設定することで、一時的な障害による不要なトラフィック切り替えを防ぎながら、適切な障害検出を実現できます。

### 問題88
Amazon Route 53を使用して、複数リージョンでのフェイルオーバー機能を実装する設定は？

A) 単一のA recordのみを使用する  
B) Health Checkを設定したWeighted routingまたはFailover routingを使用する  
C) CNAME recordのみを使用する  
D) 手動でDNSレコードを変更する

**正解**: B  
**解説**: Route 53のHealth Checkと組み合わせたWeighted routing またはFailover routingを使用することで、プライマリリージョンの障害時に自動的にセカンダリリージョンにトラフィックを切り替えられます。

### 問題89
Amazon S3で重要なデータの可用性と耐久性を最大化する設定は？

A) 単一のAZにのみデータを保存する  
B) Cross-Region Replication (CRR) とVersioningを有効にし、複数リージョンにデータを複製する  
C) ローカルストレージにのみバックアップを保存する  
D) 暗号化のみを有効にする

**正解**: B  
**解説**: CRRとVersioningを組み合わせることで、リージョン レベルの障害からデータを保護し、誤削除や破損からも復旧できます。S3は標準で99.999999999%（11 9's）の耐久性を提供します。

### 問題90
以下のAuto Scaling設定で、需要の急激な変化に対応する最適な構成は？

```json
{
  "AutoScalingGroupName": "web-tier-asg",
  "MinSize": 2,
  "MaxSize": 20,
  "DesiredCapacity": 4,
  "ScalingPolicies": [
    {
      "PolicyType": "TargetTrackingScaling",
      "TargetValue": 70,
      "MetricType": "ASGAverageCPUUtilization",
      "ScaleOutCooldown": "?",
      "ScaleInCooldown": "?"
    }
  ]
}
```

A) `ScaleOutCooldown: 600, ScaleInCooldown: 300`  
B) `ScaleOutCooldown: 300, ScaleInCooldown: 600`  
C) `ScaleOutCooldown: 60, ScaleInCooldown: 60`  
D) `ScaleOutCooldown: 1800, ScaleInCooldown: 1800`

**正解**: B  
**解説**: スケールアウトを迅速に（300秒）、スケールインを慎重に（600秒）設定することで、急激な負荷増加に素早く対応しながら、不要なスケールインを防げます。

### 問題91
Amazon RDS Multi-AZ とRead Replicasを組み合わせて、高可用性と読み取りパフォーマンスを両立する構成は？

A) Multi-AZまたはRead Replicasのいずれか一方のみを使用する  
B) Multi-AZで高可用性を確保し、Read Replicasで読み取り負荷を分散する  
C) 手動でデータベースを複製する  
D) 単一のRDSインスタンスのみを使用する

**正解**: B  
**解説**: Multi-AZは高可用性とデータ保護を提供し、Read Replicasは読み取りパフォーマンスの向上を提供します。両方を組み合わせることで包括的なソリューションを実現できます。

### 問題92
AWS Lambda関数の障害対応とデッドレターキュー（DLQ）の実装方法は？

A) エラーが発生した場合は手動で対応する  
B) 最大再試行回数を設定し、失敗したイベントをDLQに送信して後で分析・再処理する  
C) エラーを無視する  
D) Lambda関数を無効にする

**正解**: B  
**解説**: DLQを設定することで、処理に失敗したイベントを保存し、後で分析や再処理ができます。これにより、データの損失を防ぎ、システムの信頼性を向上させられます。

### 問題93
Amazon EBS ボリュームの高可用性とデータ保護を実装する最適な方法は？

A) 単一のEBSボリュームのみを使用する  
B) EBS スナップショットの自動化、RAID構成、およびクロスAZ/リージョンバックアップを実装する  
C) ローカルストレージのみを使用する  
D) 手動でデータをコピーする

**正解**: B  
**解説**: EBSスナップショットの自動化により定期的なバックアップを作成し、RAID構成で冗長性を高め、クロスリージョンバックアップで災害対策を実現できます。

### 問題94
以下のCloudFormation テンプレートで、リソースの削除保護を実装する設定は？

```yaml
AWSTemplateFormatVersion: '2010-09-09'
Resources:
  CriticalDatabase:
    Type: AWS::RDS::DBInstance
    Properties:
      DBInstanceIdentifier: critical-db
      Engine: mysql
      DBInstanceClass: db.t3.micro
      AllocatedStorage: 20
      DeletionProtection: ?
    DeletionPolicy: ?
```

A) `DeletionProtection: false, DeletionPolicy: Delete`  
B) `DeletionProtection: true, DeletionPolicy: Retain`  
C) `DeletionProtection: false, DeletionPolicy: Snapshot`  
D) 設定は不要

**正解**: B  
**解説**: DeletionProtectionをtrueに設定してリソースレベルでの削除を防ぎ、DeletionPolicyをRetainに設定してCloudFormationスタック削除時にもリソースを保持します。

### 問題95
Amazon CloudFront を使用して、グローバルなコンテンツ配信の可用性を向上させる設定は？

A) 単一のオリジンサーバーのみを使用する  
B) 複数のオリジンとOrigin Failoverを設定し、ヘルスチェックによる自動切り替えを実装する  
C) 手動でオリジンを切り替える  
D) キャッシュを無効にする

**正解**: B  
**解説**: CloudFrontの複数オリジン設定とOrigin Failoverにより、プライマリオリジンの障害時に自動的にセカンダリオリジンに切り替わり、エンドユーザーへの影響を最小化できます。

### 問題96
Amazon ElastiCache for Redis の高可用性構成を実装する最適な方法は？

A) 単一のRedisインスタンスのみを使用する  
B) Multi-AZ構成でRead Replicasを設定し、自動フェイルオーバーを有効にする  
C) 手動でフェイルオーバーを実行する  
D) バックアップを無効にする

**正解**: B  
**解説**: ElastiCache for Redis のMulti-AZ構成では、プライマリノードの障害時に自動的にRead Replicaがプライマリに昇格し、アプリケーションの中断を最小化できます。

### 問題97
AWS Backup を使用して、複数のAWSサービスの統合バックアップ戦略を実装する方法は？

A) 各サービスで個別にバックアップを設定する  
B) Backup Plans とBackup Vaultsを使用して、リソースタグベースの自動バックアップを設定する  
C) 手動でバックアップを作成する  
D) バックアップは作成しない

**正解**: B  
**解説**: AWS Backup では、Backup Plansでバックアップポリシーを定義し、リソースタグベースで複数のAWSサービス（EC2、RDS、EFS等）の統合バックアップを自動化できます。

### 問題98
以下のネットワーク構成で、VPCレベルでの可用性を向上させる設計は？

```yaml
VPC:
  CidrBlock: 10.0.0.0/16
  AvailabilityZones: ["us-east-1a", "us-east-1b", "us-east-1c"]
  
Subnets:
  PublicSubnet1: { AZ: "us-east-1a", CIDR: "10.0.1.0/24" }
  PublicSubnet2: { AZ: "us-east-1b", CIDR: "10.0.2.0/24" }
  PrivateSubnet1: { AZ: "us-east-1a", CIDR: "10.0.11.0/24" }
  PrivateSubnet2: { AZ: "us-east-1b", CIDR: "10.0.12.0/24" }
  
NATGateways: ?
```

A) `NATGateways: 1 (Single AZ)`  
B) `NATGateways: 2 (Multi-AZ, one per public subnet)`  
C) `NATGateways: 0`  
D) `NATGateways: 6 (one per subnet)`

**正解**: B  
**解説**: 各AZのPublic Subnetに1つずつNAT Gatewayを配置することで、AZ障害時でもプライベートサブネットからのインターネットアクセスを維持できます。

### 問題99
Amazon DynamoDB の高可用性とディザスタリカバリを実装する設定は？

A) 単一リージョンのみでテーブルを使用する  
B) Global Tables を設定し、Point-in-Time Recovery (PITR) を有効にする  
C) 手動でデータをバックアップする  
D) バックアップを無効にする

**正解**: B  
**解説**: DynamoDB Global Tables により複数リージョンでの自動レプリケーションを実現し、PITRにより特定時点への復旧が可能になります。これにより包括的な高可用性とディザスタリカバリを実現できます。

### 問題100
以下のAWS Step Functions状態機械で、エラーハンドリングと再試行を実装する設定は？

```json
{
  "Comment": "Critical Business Process",
  "StartAt": "ProcessData",
  "States": {
    "ProcessData": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:...",
      "Retry": [
        {
          "ErrorEquals": ["States.TaskFailed"],
          "IntervalSeconds": "?",
          "MaxAttempts": "?",
          "BackoffRate": "?"
        }
      ],
      "Catch": [
        {
          "ErrorEquals": ["States.ALL"],
          "Next": "?"
        }
      ]
    }
  }
}
```

A) `IntervalSeconds: 2, MaxAttempts: 3, BackoffRate: 2.0, Next: "FailureHandler"`  
B) `IntervalSeconds: 1, MaxAttempts: 1, BackoffRate: 1.0, Next: "ProcessData"`  
C) 再試行とエラーハンドリングは設定しない  
D) `IntervalSeconds: 60, MaxAttempts: 10, BackoffRate: 1.0, Next: "ProcessData"`

**正解**: A  
**解説**: 適切な再試行間隔（2秒）、試行回数（3回）、指数バックオフ（2.0）、そして専用のエラーハンドラーにより、一時的な障害に対する耐性と適切なエラー処理を実現できます。

---

## 📊 解答と解説一覧

### Domain 1: SDLC Automation (22%) - 問題1-22
1. B - マイクロサービスには独立したパイプライン
2. B - Parameter Storeで機密情報管理
3. B - Manual approval actionでゲート制御
4. C - Parameter Storeで環境別設定管理
5. B - Blue/Greenでダウンタイムゼロデプロイ
6. B - Git Flow戦略で並行開発管理
7. B - プラットフォーム別CodeBuildプロジェクト
8. B - KMS keyでアーティファクト暗号化
9. B - Parameter Storeから環境変数取得
10. A - CloudWatch EventsでCodeCommit監視
11. C - Rolling deploymentで段階的更新
12. B - クロスリージョンアーティファクト複製
13. A - Git LFSで大容量ファイル管理
14. B - カスタムDockerイメージをECRで管理
15. A - CloudWatch AlarmとLambdaで自動復旧
16. B - Canary deploymentで段階的トラフィック移行
17. B - プルリクエストでコンフリクト解決
18. B - 単一buildspec.ymlで複数言語対応
19. A - カスタムアクションでサードパーティ統合
20. B - IAMポリシーとリソースベースポリシー組み合わせ
21. B - S3キャッシュでビルドパフォーマンス向上
22. B - Lambda別名とバージョニングで段階的デプロイ

### Domain 2: Configuration Management and IaC (19%) - 問題23-41
23. B - Nested stacksで依存関係管理
24. B - CDKの型安全性とIDEサポート
25. B - Session Managerのセキュア接続
26. B - {{resolve:ssm:parameter-name}}で動的参照
27. B - Import resources機能でリソース組み込み
28. B - Context valuesとEnvironment-specific stacks
29. B - Maintenance WindowとPatch Group自動化
30. B - ~> 4.0でバージョン固定
31. B - ドリフト検出で手動変更検出
32. B - Run Commandで複数インスタンス実行
33. B - Environment指定でクロスアカウントデプロイ
34. B - ShouldCreateDB条件名を直接指定
35. B - Parameter Store Hierarchyで階層管理
36. B - S3リモートバックエンドとDynamoDB ロック
37. B - Nested stacksとPackaging
38. B - Config RulesとSystems Manager Compliance組み合わせ
39. B - CloudFormation Includeで段階的移行
40. B - Systems Manager Inventoryで構成情報可視化
41. D - Terraformモジュール構文すべて正しい

### Domain 3: Monitoring and Logging (15%) - 問題42-56
42. B - CloudWatch Insightsでログ分析
43. B - X-Rayで分散トレーシング
44. B - JSON形式でログ構造化
45. B - Cross-account role assumptionで統合表示
46. B - X-Ray SDKでカスタムセグメント作成
47. B - Composite Alarmで複合監視
48. B - Log Retention Policyでコスト最適化
49. B - Canary scriptsで自動監視
50. B - Event PatternでEC2状態変化監視
51. B - Log Group暗号化とIAMアクセス制限
52. B - Container Insightsで詳細監視
53. B - エクスポート機能でS3に自動保存
54. B - X-Ray Service Mapでエラー分析
55. B - Anomaly Detectionで異常自動検出
56. B - CloudWatch Insightsクエリ構文

### Domain 4: Policies and Standards Automation (10%) - 問題57-66
57. B - Organizational Config Rulesで一元監視
58. B - SCPs Deny効果で環境制限
59. B - Patch Compliance rulesで自動評価
60. B - Security Standards統合表示
61. C - ec2-security-group-attached-to-eniで未使用検出
62. B - Guardrailsで自動ポリシー適用
63. B - Guard rulesでCI/CD事前検証
64. B - Access Analyzer外部アクセス検出
65. B - 段階的アプローチでSCP適用
66. B - CloudWatch EventsとLambdaでドリフト監視

### Domain 5: Incident and Event Response (18%) - 問題67-84
67. B - Automation documentで運用自動化
68. D - EventBridge統合の全要素が必要
69. B - EC2自動復旧アクション
70. B - Session ManagerでIAM権限ベースアクセス
71. B - SNS→SQS→DLQで信頼性向上
72. B - EventBridge、Lambda、DynamoDB Streams統合
73. B - Step Functionsで複雑ワークフロー自動化
74. B - Health APIで組織レベル監視
75. B - Lambda関数でログレベル動的調整
76. B - X-RayとCloudWatch統合分析
77. B - Run Commandタグベース並列実行
78. B - Container Insights統合監視
79. B - Configでリソース変更履歴追跡
80. B - RDS障害イベント監視
81. B - Kinesis Data Streamsリアルタイム分析
82. B - Maintenance Windowで自動メンテナンス
83. B - GuardDuty EventBridge Lambda自動対応
84. B - Support API統合管理

### Domain 6: High Availability, Fault Tolerance, and Disaster Recovery (16%) - 問題85-100
85. C - RDS Multi-AZ自動フェイルオーバー
86. A - Health check grace period調整
87. B - UnhealthyThresholdCount適切設定
88. B - Route 53 Health CheckとFailover routing
89. B - S3 CRRとVersioning組み合わせ
90. B - Auto Scaling適切なCooldown設定
91. B - RDS Multi-AZとRead Replicas組み合わせ
92. B - Lambda DLQ設定
93. B - EBSスナップショット自動化とRAID構成
94. B - CloudFormation削除保護実装
95. B - CloudFront Origin Failover設定
96. B - ElastiCache Multi-AZ自動フェイルオーバー
97. B - AWS Backup統合バックアップ
98. B - Multi-AZ NAT Gateway配置
99. B - DynamoDB Global TablesとPITR
100. A - Step Functions適切エラーハンドリング

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