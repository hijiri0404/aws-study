// AWS CDK ライブラリのインポート
import * as cdk from 'aws-cdk-lib'; // CDK v2のメインライブラリ
import { Construct } from 'constructs'; // CDK constructs ライブラリ
import * as lambda from 'aws-cdk-lib/aws-lambda'; // Lambda サービス
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb'; // DynamoDB サービス
import * as apigateway from 'aws-cdk-lib/aws-apigateway'; // API Gateway サービス
import * as s3 from 'aws-cdk-lib/aws-s3'; // S3 サービス
import * as s3deploy from 'aws-cdk-lib/aws-s3-deployment'; // S3 デプロイメント
import * as cloudfront from 'aws-cdk-lib/aws-cloudfront'; // CloudFront CDN
import * as origins from 'aws-cdk-lib/aws-cloudfront-origins'; // CloudFront オリジン
import * as sqs from 'aws-cdk-lib/aws-sqs'; // SQS キューサービス
import * as ecs from 'aws-cdk-lib/aws-ecs'; // ECS コンテナサービス
import * as ec2 from 'aws-cdk-lib/aws-ec2'; // EC2/VPC サービス
import * as iam from 'aws-cdk-lib/aws-iam'; // IAM 権限管理
import * as logs from 'aws-cdk-lib/aws-logs'; // CloudWatch Logs
import * as cognito from 'aws-cdk-lib/aws-cognito'; // Cognito 認証サービス
import * as lambdaEventSources from 'aws-cdk-lib/aws-lambda-event-sources'; // Lambda イベントソース

// 小説ダウンローダーのメインスタッククラス
export class NovelDownloaderStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props); // 親クラス（Stack）のコンストラクタを呼び出し

    // ======================
    // 1. DynamoDB テーブル作成
    // ======================

    // 作品メタデータテーブル
    const worksTable = new dynamodb.Table(this, 'WorksTable', {
      tableName: 'novel-works', // テーブル名
      partitionKey: { // パーティションキー（プライマリキー）
        name: 'work_id', // 作品ID
        type: dynamodb.AttributeType.STRING // 文字列型
      },
      sortKey: { // ソートキー（範囲キー）
        name: 'metadata_type', // メタデータタイプ（info, chapters等）
        type: dynamodb.AttributeType.STRING // 文字列型
      },
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST, // オンデマンド課金
      removalPolicy: cdk.RemovalPolicy.RETAIN, // スタック削除時もテーブル保持
      pointInTimeRecovery: true, // ポイントインタイム復旧を有効化
      encryption: dynamodb.TableEncryption.AWS_MANAGED, // AWS管理の暗号化
    });

    // ダウンロード履歴テーブル
    const downloadsTable = new dynamodb.Table(this, 'DownloadsTable', {
      tableName: 'novel-downloads', // テーブル名
      partitionKey: { // パーティションキー
        name: 'user_id', // ユーザーID
        type: dynamodb.AttributeType.STRING // 文字列型
      },
      sortKey: { // ソートキー
        name: 'task_id', // タスクID（ダウンロードタスクの一意識別子）
        type: dynamodb.AttributeType.STRING // 文字列型
      },
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST, // オンデマンド課金
      removalPolicy: cdk.RemovalPolicy.DESTROY, // スタック削除時にテーブルも削除
      pointInTimeRecovery: true, // ポイントインタイム復旧を有効化
      encryption: dynamodb.TableEncryption.AWS_MANAGED, // AWS管理の暗号化
    });

    // ダウンロードテーブルにGSI（グローバルセカンダリインデックス）を追加
    downloadsTable.addGlobalSecondaryIndex({
      indexName: 'work-id-index', // インデックス名
      partitionKey: { // GSIのパーティションキー
        name: 'work_id', // 作品ID
        type: dynamodb.AttributeType.STRING // 文字列型
      },
      sortKey: { // GSIのソートキー
        name: 'created_at', // 作成日時
        type: dynamodb.AttributeType.STRING // 文字列型（ISO 8601形式）
      },
      projectionType: dynamodb.ProjectionType.ALL, // 全属性を投影
    });

    // ユーザー管理テーブル
    const usersTable = new dynamodb.Table(this, 'UsersTable', {
      tableName: 'novel-users', // テーブル名
      partitionKey: { // パーティションキー
        name: 'user_id', // ユーザーID
        type: dynamodb.AttributeType.STRING // 文字列型
      },
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST, // オンデマンド課金
      removalPolicy: cdk.RemovalPolicy.RETAIN, // スタック削除時もテーブル保持
      pointInTimeRecovery: true, // ポイントインタイム復旧を有効化
      encryption: dynamodb.TableEncryption.AWS_MANAGED, // AWS管理の暗号化
    });

    // ======================
    // 2. S3 バケット作成
    // ======================

    // フロントエンド用S3バケット（静的ウェブサイトホスティング）
    const frontendBucket = new s3.Bucket(this, 'FrontendBucket', {
      bucketName: `novel-downloader-frontend-${this.account}`, // バケット名（アカウントID付き）
      websiteIndexDocument: 'index.html', // インデックスドキュメント
      websiteErrorDocument: 'error.html', // エラードキュメント
      publicReadAccess: true, // パブリック読み取りアクセス許可
      blockPublicAccess: s3.BlockPublicAccess.BLOCK_ACLS, // ACLのみブロック、バケットポリシーは許可
      removalPolicy: cdk.RemovalPolicy.DESTROY, // スタック削除時にバケットも削除
      autoDeleteObjects: true, // オブジェクト自動削除を有効化
      encryption: s3.BucketEncryption.S3_MANAGED, // S3管理の暗号化
      enforceSSL: true, // SSL/TLS接続を強制
    });

    // ダウンロードファイル保存用S3バケット
    const storagesBucket = new s3.Bucket(this, 'StorageBucket', {
      bucketName: `novel-downloader-storage-${this.account}`, // バケット名（アカウントID付き）
      versioned: true, // バージョニング有効化
      removalPolicy: cdk.RemovalPolicy.RETAIN, // スタック削除時もバケット保持
      encryption: s3.BucketEncryption.S3_MANAGED, // S3管理の暗号化
      enforceSSL: true, // SSL/TLS接続を強制
      lifecycleRules: [{ // ライフサイクルルール設定
        id: 'DeleteOldFiles', // ルールID
        enabled: true, // ルール有効化
        expiration: cdk.Duration.days(90), // 90日後に削除
        noncurrentVersionExpiration: cdk.Duration.days(30), // 旧バージョンは30日後に削除
      }],
    });

    // ======================
    // 3. SQS キュー作成
    // ======================

    // デッドレターキュー（失敗したメッセージの保存先）
    const deadLetterQueue = new sqs.Queue(this, 'DeadLetterQueue', {
      queueName: 'novel-downloader-dlq', // キュー名
      retentionPeriod: cdk.Duration.days(14), // メッセージ保持期間（14日）
      encryption: sqs.QueueEncryption.SQS_MANAGED, // SQS管理の暗号化
    });

    // ダウンロード処理用メインキュー
    const downloadQueue = new sqs.Queue(this, 'DownloadQueue', {
      queueName: 'novel-downloader-queue', // キュー名
      visibilityTimeout: cdk.Duration.minutes(15), // 可視性タイムアウト（15分）
      deadLetterQueue: { // デッドレターキュー設定
        queue: deadLetterQueue, // 上記で作成したDLQ
        maxReceiveCount: 3, // 最大受信回数（3回失敗でDLQに移動）
      },
      encryption: sqs.QueueEncryption.SQS_MANAGED, // SQS管理の暗号化
    });

    // ======================
    // 4. Cognito ユーザープール作成
    // ======================

    // ユーザープール（認証用）
    const userPool = new cognito.UserPool(this, 'UserPool', {
      userPoolName: 'novel-downloader-users', // ユーザープール名
      selfSignUpEnabled: true, // セルフサインアップ有効
      signInAliases: { // サインイン方法
        email: true, // メールアドレスでサインイン可能
        username: true, // ユーザー名でサインイン可能
      },
      autoVerify: { // 自動検証設定
        email: true, // メール自動検証有効
      },
      passwordPolicy: { // パスワードポリシー
        minLength: 8, // 最小文字数
        requireLowercase: true, // 小文字必須
        requireUppercase: true, // 大文字必須
        requireDigits: true, // 数字必須
        requireSymbols: false, // 記号は任意
      },
      accountRecovery: cognito.AccountRecovery.EMAIL_ONLY, // アカウント復旧はメールのみ
      removalPolicy: cdk.RemovalPolicy.DESTROY, // スタック削除時にユーザープールも削除
    });

    // ユーザープールクライアント（フロントエンドアプリ用）
    const userPoolClient = new cognito.UserPoolClient(this, 'UserPoolClient', {
      userPool: userPool, // 上記で作成したユーザープール
      userPoolClientName: 'novel-downloader-client', // クライアント名
      generateSecret: false, // クライアントシークレット生成しない（SPAのため）
      authFlows: { // 認証フロー設定
        userSrp: true, // SRPフロー有効
        userPassword: true, // パスワードフロー有効
      },
      oAuth: { // OAuth設定
        flows: { // OAuthフロー
          authorizationCodeGrant: true, // 認可コードグラント有効
          implicitCodeGrant: true, // インプリシットグラント有効
        },
        scopes: [ // スコープ設定
          cognito.OAuthScope.OPENID, // OpenIDスコープ
          cognito.OAuthScope.EMAIL, // メールスコープ
          cognito.OAuthScope.PROFILE, // プロファイルスコープ
        ],
        callbackUrls: [ // コールバックURL
          'http://localhost:3000', // 開発環境
          `https://${frontendBucket.bucketWebsiteDomainName}`, // 本番環境
        ],
        logoutUrls: [ // ログアウトURL
          'http://localhost:3000', // 開発環境
          `https://${frontendBucket.bucketWebsiteDomainName}`, // 本番環境
        ],
      },
    });

    // ======================
    // 5. Lambda 関数用のIAMロール作成
    // ======================

    // Lambda実行ロール
    const lambdaExecutionRole = new iam.Role(this, 'LambdaExecutionRole', {
      roleName: 'NovelDownloaderLambdaRole', // ロール名
      assumedBy: new iam.ServicePrincipal('lambda.amazonaws.com'), // Lambda サービスが引き受け可能
      managedPolicies: [ // 管理ポリシーをアタッチ
        iam.ManagedPolicy.fromAwsManagedPolicyName('service-role/AWSLambdaBasicExecutionRole'), // 基本実行権限
        iam.ManagedPolicy.fromAwsManagedPolicyName('service-role/AWSLambdaVPCAccessExecutionRole'), // VPCアクセス権限
      ],
      inlinePolicies: { // インラインポリシー
        DynamoDBAccess: new iam.PolicyDocument({ // DynamoDB アクセス権限
          statements: [
            new iam.PolicyStatement({
              effect: iam.Effect.ALLOW, // 許可
              actions: [ // 許可するアクション
                'dynamodb:GetItem', // アイテム取得
                'dynamodb:PutItem', // アイテム挿入
                'dynamodb:UpdateItem', // アイテム更新
                'dynamodb:DeleteItem', // アイテム削除
                'dynamodb:Query', // クエリ実行
                'dynamodb:Scan', // スキャン実行
              ],
              resources: [ // 対象リソース
                worksTable.tableArn, // 作品テーブル
                `${worksTable.tableArn}/index/*`, // 作品テーブルのインデックス
                downloadsTable.tableArn, // ダウンロードテーブル
                `${downloadsTable.tableArn}/index/*`, // ダウンロードテーブルのインデックス
                usersTable.tableArn, // ユーザーテーブル
              ],
            }),
          ],
        }),
        S3Access: new iam.PolicyDocument({ // S3 アクセス権限
          statements: [
            new iam.PolicyStatement({
              effect: iam.Effect.ALLOW, // 許可
              actions: [ // 許可するアクション
                's3:GetObject', // オブジェクト取得
                's3:PutObject', // オブジェクト配置
                's3:DeleteObject', // オブジェクト削除
                's3:ListBucket', // バケット一覧取得
              ],
              resources: [ // 対象リソース
                storagesBucket.bucketArn, // ストレージバケット
                `${storagesBucket.bucketArn}/*`, // ストレージバケット内全オブジェクト
              ],
            }),
          ],
        }),
        SQSAccess: new iam.PolicyDocument({ // SQS アクセス権限
          statements: [
            new iam.PolicyStatement({
              effect: iam.Effect.ALLOW, // 許可
              actions: [ // 許可するアクション
                'sqs:SendMessage', // メッセージ送信
                'sqs:ReceiveMessage', // メッセージ受信
                'sqs:DeleteMessage', // メッセージ削除
                'sqs:GetQueueAttributes', // キュー属性取得
              ],
              resources: [ // 対象リソース
                downloadQueue.queueArn, // ダウンロードキュー
                deadLetterQueue.queueArn, // デッドレターキュー
              ],
            }),
          ],
        }),
      },
    });

    // ======================
    // 6. Lambda 関数作成
    // ======================

    // API ハンドラー Lambda 関数
    const apiHandler = new lambda.Function(this, 'ApiHandler', {
      functionName: 'novel-downloader-api-handler', // 関数名
      runtime: lambda.Runtime.PYTHON_3_11, // Python 3.11 ランタイム
      code: lambda.Code.fromAsset('lambda/api-handler'), // ソースコードディレクトリ
      handler: 'lambda_handler.lambda_handler', // ハンドラー関数
      timeout: cdk.Duration.seconds(30), // タイムアウト（30秒）
      memorySize: 512, // メモリサイズ（512MB）
      role: lambdaExecutionRole, // 上記で作成したIAMロール
      environment: { // 環境変数
        WORKS_TABLE_NAME: worksTable.tableName, // 作品テーブル名
        DOWNLOADS_TABLE_NAME: downloadsTable.tableName, // ダウンロードテーブル名
        USERS_TABLE_NAME: usersTable.tableName, // ユーザーテーブル名
        STORAGE_BUCKET_NAME: storagesBucket.bucketName, // ストレージバケット名
        DOWNLOAD_QUEUE_URL: downloadQueue.queueUrl, // ダウンロードキューURL
        USER_POOL_ID: userPool.userPoolId, // ユーザープールID
        USER_POOL_CLIENT_ID: userPoolClient.userPoolClientId, // ユーザープールクライアントID
      },
      logRetention: logs.RetentionDays.ONE_WEEK, // ログ保持期間（1週間）
    });

    // ダウンロード処理 Lambda 関数
    const downloadProcessor = new lambda.Function(this, 'DownloadProcessor', {
      functionName: 'novel-downloader-processor', // 関数名
      runtime: lambda.Runtime.PYTHON_3_11, // Python 3.11 ランタイム
      code: lambda.Code.fromAsset('lambda/download-processor'), // ソースコードディレクトリ
      handler: 'lambda_handler.lambda_handler', // ハンドラー関数
      timeout: cdk.Duration.minutes(15), // タイムアウト（15分）
      memorySize: 1024, // メモリサイズ（1GB）
      role: lambdaExecutionRole, // 上記で作成したIAMロール
      environment: { // 環境変数
        WORKS_TABLE_NAME: worksTable.tableName, // 作品テーブル名
        DOWNLOADS_TABLE_NAME: downloadsTable.tableName, // ダウンロードテーブル名
        STORAGE_BUCKET_NAME: storagesBucket.bucketName, // ストレージバケット名
        DOWNLOAD_QUEUE_URL: downloadQueue.queueUrl, // ダウンロードキューURL
      },
      logRetention: logs.RetentionDays.ONE_MONTH, // ログ保持期間（1ヶ月）
    });

    // SQSをLambdaのイベントソースとして設定
    downloadProcessor.addEventSource(new lambdaEventSources.SqsEventSource(downloadQueue, {
      batchSize: 1, // バッチサイズ（1メッセージずつ処理）
      maxBatchingWindow: cdk.Duration.seconds(5), // 最大バッチ待機時間（5秒）
      reportBatchItemFailures: true, // バッチアイテム失敗報告を有効化
    }));

    // ステータスチェッカー Lambda 関数
    const statusChecker = new lambda.Function(this, 'StatusChecker', {
      functionName: 'novel-downloader-status-checker', // 関数名
      runtime: lambda.Runtime.PYTHON_3_11, // Python 3.11 ランタイム
      code: lambda.Code.fromAsset('lambda/status-checker'), // ソースコードディレクトリ
      handler: 'lambda_handler.lambda_handler', // ハンドラー関数
      timeout: cdk.Duration.seconds(10), // タイムアウト（10秒）
      memorySize: 256, // メモリサイズ（256MB）
      role: lambdaExecutionRole, // 上記で作成したIAMロール
      environment: { // 環境変数
        DOWNLOADS_TABLE_NAME: downloadsTable.tableName, // ダウンロードテーブル名
        STORAGE_BUCKET_NAME: storagesBucket.bucketName, // ストレージバケット名
      },
      logRetention: logs.RetentionDays.ONE_WEEK, // ログ保持期間（1週間）
    });

    // Cognito認証用のオーソライザーLambda関数
    const cognitoAuthorizer = new lambda.Function(this, 'CognitoAuthorizer', {
      functionName: 'novel-downloader-cognito-authorizer', // 関数名
      runtime: lambda.Runtime.PYTHON_3_11, // Python 3.11 ランタイム
      code: lambda.Code.fromAsset('lambda/cognito-authorizer'), // ソースコードディレクトリ
      handler: 'lambda_handler.lambda_handler', // ハンドラー関数
      timeout: cdk.Duration.seconds(10), // タイムアウト（10秒）
      memorySize: 256, // メモリサイズ（256MB）
      role: lambdaExecutionRole, // 上記で作成したIAMロール
      environment: { // 環境変数
        USER_POOL_ID: userPool.userPoolId, // ユーザープールID
        USER_POOL_CLIENT_ID: userPoolClient.userPoolClientId, // ユーザープールクライアントID
      },
      logRetention: logs.RetentionDays.ONE_WEEK, // ログ保持期間（1週間）
    });

    // ======================
    // 7. API Gateway 作成
    // ======================

    // Lambda オーソライザー作成
    const authorizer = new apigateway.TokenAuthorizer(this, 'CognitoTokenAuthorizer', {
      handler: cognitoAuthorizer, // 上記で作成したオーソライザーLambda
      authorizerName: 'CognitoAuthorizer', // オーソライザー名
      resultsCacheTtl: cdk.Duration.minutes(5), // 結果キャッシュTTL（5分）
      identitySource: 'method.request.header.Authorization', // 認証トークンの取得元ヘッダー
    });

    // REST API 作成
    const api = new apigateway.RestApi(this, 'NovelDownloaderApi', {
      restApiName: 'Novel Downloader API', // API名
      description: 'REST API for Novel Downloader Service', // API説明
      defaultCorsPreflightOptions: { // CORS設定
        allowOrigins: apigateway.Cors.ALL_ORIGINS, // 全オリジン許可
        allowMethods: apigateway.Cors.ALL_METHODS, // 全メソッド許可
        allowHeaders: [ // 許可ヘッダー
          'Content-Type',
          'X-Amz-Date',
          'Authorization',
          'X-Api-Key',
          'X-Amz-Security-Token',
        ],
      },
      cloudWatchRole: true, // CloudWatch ロール有効化
      deploy: true, // 自動デプロイ有効化
      deployOptions: { // デプロイオプション
        stageName: 'prod', // ステージ名
        throttlingRateLimit: 100, // スロットリングレート制限（100 req/sec）
        throttlingBurstLimit: 200, // スロットリングバースト制限（200 req）
        loggingLevel: apigateway.MethodLoggingLevel.INFO, // ログレベル
        dataTraceEnabled: true, // データトレース有効化
        metricsEnabled: true, // メトリクス有効化
      },
    });

    // API エンドポイントグループ作成

    // /api リソース
    const apiResource = api.root.addResource('api'); // /api

    // /api/download リソース
    const downloadResource = apiResource.addResource('download'); // /api/download
    downloadResource.addMethod('POST', new apigateway.LambdaIntegration(apiHandler), { // POST /api/download
      authorizer: authorizer, // Cognito認証が必要
      requestValidator: new apigateway.RequestValidator(this, 'DownloadRequestValidator', { // リクエストバリデーター
        restApi: api,
        validateRequestBody: true, // リクエストボディ検証
        validateRequestParameters: false, // リクエストパラメータ検証なし
      }),
      requestModels: { // リクエストモデル
        'application/json': new apigateway.Model(this, 'DownloadRequestModel', { // JSONモデル
          restApi: api,
          modelName: 'DownloadRequest', // モデル名
          contentType: 'application/json',
          schema: { // JSONスキーマ
            type: apigateway.JsonSchemaType.OBJECT,
            properties: {
              work_id: { // 作品ID
                type: apigateway.JsonSchemaType.STRING,
                minLength: 1,
                maxLength: 50,
              },
              options: { // オプション
                type: apigateway.JsonSchemaType.OBJECT,
                properties: {
                  start_chapter: { type: apigateway.JsonSchemaType.INTEGER },
                  end_chapter: { type: apigateway.JsonSchemaType.INTEGER },
                  force_update: { type: apigateway.JsonSchemaType.BOOLEAN },
                },
              },
            },
            required: ['work_id'], // 必須フィールド
          },
        }),
      },
    });

    // /api/status/{task_id} リソース
    const statusResource = apiResource.addResource('status'); // /api/status
    const statusTaskResource = statusResource.addResource('{task_id}'); // /api/status/{task_id}
    statusTaskResource.addMethod('GET', new apigateway.LambdaIntegration(statusChecker), { // GET /api/status/{task_id}
      authorizer: authorizer, // Cognito認証が必要
      requestParameters: { // リクエストパラメータ
        'method.request.path.task_id': true, // task_id パラメータ必須
      },
    });

    // /api/works リソース
    const worksResource = apiResource.addResource('works'); // /api/works
    worksResource.addMethod('GET', new apigateway.LambdaIntegration(apiHandler), { // GET /api/works
      authorizer: authorizer, // Cognito認証が必要
    });

    // /api/health リソース（ヘルスチェック用、認証不要）
    const healthResource = apiResource.addResource('health'); // /api/health
    healthResource.addMethod('GET', new apigateway.LambdaIntegration(apiHandler)); // GET /api/health（認証不要）

    // ======================
    // 8. CloudFront 配信設定
    // ======================

    // CloudFront ディストリビューション作成
    const distribution = new cloudfront.Distribution(this, 'Distribution', {
      comment: 'Novel Downloader Frontend Distribution', // コメント
      defaultRootObject: 'index.html', // デフォルトルートオブジェクト
      priceClass: cloudfront.PriceClass.PRICE_CLASS_100, // 料金クラス（安価な地域のみ）
      httpVersion: cloudfront.HttpVersion.HTTP2_AND_3, // HTTP/2, HTTP/3対応
      defaultBehavior: { // デフォルトビヘイビア
        origin: new origins.S3Origin(frontendBucket), // S3オリジン
        allowedMethods: cloudfront.AllowedMethods.ALLOW_GET_HEAD, // GET, HEADメソッドのみ許可
        viewerProtocolPolicy: cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS, // HTTPS強制
        cachePolicy: cloudfront.CachePolicy.CACHING_OPTIMIZED, // キャッシュ最適化
        compress: true, // 圧縮有効化
      },
      additionalBehaviors: { // 追加ビヘイビア
        '/api/*': { // API パス
          origin: new origins.RestApiOrigin(api), // API Gateway オリジン
          allowedMethods: cloudfront.AllowedMethods.ALLOW_ALL, // 全メソッド許可
          viewerProtocolPolicy: cloudfront.ViewerProtocolPolicy.HTTPS_ONLY, // HTTPS必須
          cachePolicy: cloudfront.CachePolicy.CACHING_DISABLED, // キャッシュ無効化
          originRequestPolicy: cloudfront.OriginRequestPolicy.ALL_VIEWER_EXCEPT_HOST_HEADER, // ビューワーリクエスト転送
        },
      },
      errorResponses: [ // エラーレスポンス設定
        {
          httpStatus: 404, // 404エラー
          responseHttpStatus: 200, // 200で返す
          responsePagePath: '/index.html', // SPAのindex.htmlを返す
          ttl: cdk.Duration.minutes(5), // TTL 5分
        },
        {
          httpStatus: 403, // 403エラー
          responseHttpStatus: 200, // 200で返す
          responsePagePath: '/index.html', // SPAのindex.htmlを返す
          ttl: cdk.Duration.minutes(5), // TTL 5分
        },
      ],
    });

    // ======================
    // 9. ECS Fargate クラスター（重い処理用）
    // ======================

    // VPC作成（ECS用）
    const vpc = new ec2.Vpc(this, 'NovelDownloaderVpc', {
      vpcName: 'novel-downloader-vpc', // VPC名
      ipAddresses: ec2.IpAddresses.cidr('10.0.0.0/16'), // CIDR ブロック
      maxAzs: 2, // 最大アベイラビリティゾーン数
      natGateways: 1, // NAT ゲートウェイ数（コスト削減のため1つ）
      subnetConfiguration: [ // サブネット設定
        {
          cidrMask: 24, // サブネットマスク
          name: 'Public', // パブリックサブネット
          subnetType: ec2.SubnetType.PUBLIC,
        },
        {
          cidrMask: 24, // サブネットマスク
          name: 'Private', // プライベートサブネット
          subnetType: ec2.SubnetType.PRIVATE_WITH_EGRESS,
        },
      ],
    });

    // ECS クラスター作成
    const cluster = new ecs.Cluster(this, 'NovelDownloaderCluster', {
      clusterName: 'novel-downloader-cluster', // クラスター名
      vpc: vpc, // 上記で作成したVPC
      containerInsights: true, // Container Insights有効化
    });

    // ECS タスク実行ロール
    const ecsTaskExecutionRole = new iam.Role(this, 'EcsTaskExecutionRole', {
      roleName: 'NovelDownloaderEcsTaskExecutionRole', // ロール名
      assumedBy: new iam.ServicePrincipal('ecs-tasks.amazonaws.com'), // ECS タスクが引き受け可能
      managedPolicies: [ // 管理ポリシー
        iam.ManagedPolicy.fromAwsManagedPolicyName('service-role/AmazonECSTaskExecutionRolePolicy'), // ECS実行権限
      ],
    });

    // ECS タスクロール（アプリケーション用）
    const ecsTaskRole = new iam.Role(this, 'EcsTaskRole', {
      roleName: 'NovelDownloaderEcsTaskRole', // ロール名
      assumedBy: new iam.ServicePrincipal('ecs-tasks.amazonaws.com'), // ECS タスクが引き受け可能
      inlinePolicies: { // インラインポリシー
        DynamoDBAccess: new iam.PolicyDocument({ // DynamoDB アクセス権限
          statements: [
            new iam.PolicyStatement({
              effect: iam.Effect.ALLOW,
              actions: ['dynamodb:*'], // DynamoDB 全権限
              resources: [worksTable.tableArn, downloadsTable.tableArn, usersTable.tableArn],
            }),
          ],
        }),
        S3Access: new iam.PolicyDocument({ // S3 アクセス権限
          statements: [
            new iam.PolicyStatement({
              effect: iam.Effect.ALLOW,
              actions: ['s3:*'], // S3 全権限
              resources: [storagesBucket.bucketArn, `${storagesBucket.bucketArn}/*`],
            }),
          ],
        }),
        SQSAccess: new iam.PolicyDocument({ // SQS アクセス権限
          statements: [
            new iam.PolicyStatement({
              effect: iam.Effect.ALLOW,
              actions: ['sqs:*'], // SQS 全権限
              resources: [downloadQueue.queueArn, deadLetterQueue.queueArn],
            }),
          ],
        }),
      },
    });

    // ECS タスク定義
    const taskDefinition = new ecs.FargateTaskDefinition(this, 'TaskDefinition', {
      family: 'novel-downloader-task', // タスクファミリー名
      cpu: 1024, // CPU（1 vCPU）
      memoryLimitMiB: 2048, // メモリ（2GB）
      executionRole: ecsTaskExecutionRole, // 実行ロール
      taskRole: ecsTaskRole, // タスクロール
    });

    // コンテナ定義
    const container = taskDefinition.addContainer('NovelDownloaderContainer', {
      containerName: 'novel-downloader', // コンテナ名
      image: ecs.ContainerImage.fromAsset('docker'), // Dockerイメージ（ローカルビルド）
      logging: ecs.LogDrivers.awsLogs({ // ログドライバー
        streamPrefix: 'novel-downloader', // ログストリームプレフィックス
        logRetention: logs.RetentionDays.ONE_MONTH, // ログ保持期間（1ヶ月）
      }),
      environment: { // 環境変数
        WORKS_TABLE_NAME: worksTable.tableName, // 作品テーブル名
        DOWNLOADS_TABLE_NAME: downloadsTable.tableName, // ダウンロードテーブル名
        STORAGE_BUCKET_NAME: storagesBucket.bucketName, // ストレージバケット名
        DOWNLOAD_QUEUE_URL: downloadQueue.queueUrl, // ダウンロードキューURL
        AWS_DEFAULT_REGION: this.region, // AWSリージョン
      },
    });

    // ======================
    // 10. CloudFormation出力値設定
    // ======================

    // API Gateway エンドポイントURL
    new cdk.CfnOutput(this, 'ApiGatewayUrl', {
      description: 'API Gateway endpoint URL', // 説明
      value: api.url, // API Gateway URL
      exportName: 'NovelDownloader-ApiGatewayUrl', // エクスポート名
    });

    // CloudFront ディストリビューションURL
    new cdk.CfnOutput(this, 'CloudFrontUrl', {
      description: 'CloudFront distribution URL', // 説明
      value: `https://${distribution.distributionDomainName}`, // CloudFront URL
      exportName: 'NovelDownloader-CloudFrontUrl', // エクスポート名
    });

    // S3 ウェブサイトURL
    new cdk.CfnOutput(this, 'S3WebsiteUrl', {
      description: 'S3 website URL', // 説明
      value: frontendBucket.bucketWebsiteUrl, // S3 ウェブサイトURL
      exportName: 'NovelDownloader-S3WebsiteUrl', // エクスポート名
    });

    // Cognito ユーザープールID
    new cdk.CfnOutput(this, 'CognitoUserPoolId', {
      description: 'Cognito User Pool ID', // 説明
      value: userPool.userPoolId, // ユーザープールID
      exportName: 'NovelDownloader-UserPoolId', // エクスポート名
    });

    // Cognito ユーザープールクライアントID
    new cdk.CfnOutput(this, 'CognitoUserPoolClientId', {
      description: 'Cognito User Pool Client ID', // 説明
      value: userPoolClient.userPoolClientId, // ユーザープールクライアントID
      exportName: 'NovelDownloader-UserPoolClientId', // エクスポート名
    });

    // DynamoDB テーブル名（デバッグ用）
    new cdk.CfnOutput(this, 'WorksTableName', {
      description: 'DynamoDB Works Table Name', // 説明
      value: worksTable.tableName, // 作品テーブル名
      exportName: 'NovelDownloader-WorksTableName', // エクスポート名
    });

    new cdk.CfnOutput(this, 'DownloadsTableName', {
      description: 'DynamoDB Downloads Table Name', // 説明
      value: downloadsTable.tableName, // ダウンロードテーブル名
      exportName: 'NovelDownloader-DownloadsTableName', // エクスポート名
    });

    // S3 バケット名
    new cdk.CfnOutput(this, 'StorageBucketName', {
      description: 'S3 Storage Bucket Name', // 説明
      value: storagesBucket.bucketName, // ストレージバケット名
      exportName: 'NovelDownloader-StorageBucketName', // エクスポート名
    });

    // SQS キューURL
    new cdk.CfnOutput(this, 'DownloadQueueUrl', {
      description: 'SQS Download Queue URL', // 説明
      value: downloadQueue.queueUrl, // ダウンロードキューURL
      exportName: 'NovelDownloader-DownloadQueueUrl', // エクスポート名
    });

    // ECS クラスター名
    new cdk.CfnOutput(this, 'EcsClusterName', {
      description: 'ECS Cluster Name', // 説明
      value: cluster.clusterName, // ECS クラスター名
      exportName: 'NovelDownloader-EcsClusterName', // エクスポート名
    });
  }
}