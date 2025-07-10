#!/usr/bin/env node
// AWS CDK アプリケーションのエントリーポイント
// このファイルでスタックをインスタンス化し、CDKアプリに追加する

import 'source-map-support/register'; // TypeScriptのソースマップサポートを有効化
import * as cdk from 'aws-cdk-lib'; // AWS CDK v2のメインライブラリ
import { NovelDownloaderStack } from '../lib/novel-downloader-stack'; // メインスタッククラスをインポート

// CDKアプリケーションインスタンスを作成
const app = new cdk.App();

// 小説ダウンローダーのメインスタックを作成
// スタック名: NovelDownloaderStack
// 環境設定: 環境変数またはデフォルト値を使用
new NovelDownloaderStack(app, 'NovelDownloaderStack', {
  // スタックの説明
  description: 'AWS CDK Stack for Novel Downloader Service - Serverless architecture with Lambda, DynamoDB, API Gateway',
  
  // デプロイ先の環境設定
  env: {
    // AWSアカウントID（環境変数から取得、未設定の場合はundefined）
    account: process.env.CDK_DEFAULT_ACCOUNT,
    // AWSリージョン（環境変数から取得、未設定の場合はundefined）
    region: process.env.CDK_DEFAULT_REGION,
  },

  // スタックタグの設定（請求管理やリソース管理に使用）
  tags: {
    Project: 'NovelDownloader', // プロジェクト名
    Environment: 'Production',   // 環境区分
    Owner: 'DevTeam',           // 所有者
    CostCenter: 'Engineering',   // コストセンター
  },
});