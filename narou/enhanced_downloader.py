#!/usr/bin/env python3
"""
小説家になろう - 拡張版ダウンロードスクリプト
作品別進捗管理・更新検知・増分ダウンロード対応
"""

import requests
import time
import sys
import os
import re
import json
import argparse
from datetime import datetime
from urllib.parse import urljoin
from bs4 import BeautifulSoup

class EnhancedNovelDownloader:
    def __init__(self, work_id, output_dir="/home/hijiri/claude/claude/narou", start_chapter=1, end_chapter=None, force_update=False):
        self.work_id = work_id
        self.base_url = f"https://ncode.syosetu.com/{work_id}/"
        self.output_dir = output_dir
        self.start_chapter = start_chapter
        self.end_chapter = end_chapter
        self.force_update = force_update
        self.novel_title = None
        self.author_name = None
        self.failed_chapters = []
        
        # データ管理用ディレクトリ
        self.data_dir = os.path.join(output_dir, "data")
        os.makedirs(self.data_dir, exist_ok=True)
        
        # 作品管理用データベースファイル（dataフォルダ内）
        self.db_file = os.path.join(self.data_dir, "novels_database.json")
        self.work_progress_file = os.path.join(self.data_dir, f"progress_{work_id}.json")
        
        # 初期化
        self.ensure_database()
        
    def ensure_database(self):
        """データベースファイルが存在しない場合は作成"""
        if not os.path.exists(self.db_file):
            initial_db = {
                "created_at": datetime.now().isoformat(),
                "works": {}
            }
            with open(self.db_file, 'w', encoding='utf-8') as f:
                json.dump(initial_db, f, ensure_ascii=False, indent=2)
    
    def load_database(self):
        """データベースをロード"""
        with open(self.db_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def save_database(self, db_data):
        """データベースを保存"""
        with open(self.db_file, 'w', encoding='utf-8') as f:
            json.dump(db_data, f, ensure_ascii=False, indent=2)
    
    def get_work_info(self):
        """データベースから作品情報を取得"""
        db = self.load_database()
        return db["works"].get(self.work_id, {})
    
    def update_work_info(self, info):
        """データベースの作品情報を更新"""
        db = self.load_database()
        if self.work_id not in db["works"]:
            db["works"][self.work_id] = {}
        
        db["works"][self.work_id].update(info)
        db["works"][self.work_id]["last_updated"] = datetime.now().isoformat()
        self.save_database(db)
    
    def get_novel_info(self):
        """作品情報（タイトル・作者・章数）を取得"""
        try:
            print(f"作品情報取得中: {self.base_url}")
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'ja,en-US;q=0.9,en;q=0.8',
            }
            
            response = requests.get(self.base_url, timeout=30, headers=headers)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # タイトルの抽出
            title_selectors = [
                'h1.p-novel__title',
                'h1',
                '.novel_title',
                'title',
            ]
            
            for selector in title_selectors:
                element = soup.select_one(selector)
                if element:
                    title_text = element.get_text(strip=True)
                    if selector == 'title':
                        title_text = title_text.split('小説家になろう')[0].strip()
                        title_text = title_text.split(' - ')[0].strip()
                    if title_text and title_text != '小説家になろう':
                        self.novel_title = title_text
                        break
            
            if not self.novel_title:
                self.novel_title = f"作品ID_{self.work_id}"
            
            # 作者名の抽出
            author_selectors = [
                '.p-novel__author a',
                '.novel_writername a',
                'a[href*="/user/"]',
            ]
            
            for selector in author_selectors:
                element = soup.select_one(selector)
                if element:
                    self.author_name = element.get_text(strip=True)
                    break
            
            if not self.author_name:
                self.author_name = "不明"
            
            # 最終更新日の取得
            last_update = None
            update_selectors = [
                '.p-novel__update',
                '.novel_update',
                '[class*="update"]'
            ]
            
            for selector in update_selectors:
                element = soup.select_one(selector)
                if element:
                    last_update = element.get_text(strip=True)
                    break
            
            # 章数の検出
            if not self.end_chapter:
                # 目次ページからの章数検出（制限あり）
                chapter_links = soup.select('a[href*="/' + self.work_id + '/"]')
                chapter_numbers = []
                
                for link in chapter_links:
                    href = link.get('href', '')
                    match = re.search(rf'/{self.work_id}/(\d+)/', href)
                    if match:
                        chapter_numbers.append(int(match.group(1)))
                
                # 目次で100章しか表示されない場合があるため、二分探索で実際の最大値を検出
                if chapter_numbers:
                    max_from_links = max(chapter_numbers)
                    # 100章丁度の場合は、それより多い可能性があるので二分探索実行
                    if max_from_links == 100:
                        print(f"目次から検出: {max_from_links}章（制限の可能性あり）")
                        self.end_chapter = self.detect_max_chapter()
                    else:
                        self.end_chapter = max_from_links
                else:
                    self.end_chapter = self.detect_max_chapter()
            
            # 作品情報をデータベースに保存
            work_info = {
                "title": self.novel_title,
                "author": self.author_name,
                "total_chapters": self.end_chapter,
                "web_last_update": last_update,
                "first_downloaded": datetime.now().isoformat()
            }
            
            # 既存の作品情報がある場合は一部情報を保持
            existing_info = self.get_work_info()
            if existing_info:
                work_info["first_downloaded"] = existing_info.get("first_downloaded", work_info["first_downloaded"])
            
            self.update_work_info(work_info)
            
            print(f"作品名: {self.novel_title}")
            print(f"作者: {self.author_name}")
            print(f"検出章数: {self.end_chapter}章")
            if last_update:
                print(f"WEB最終更新: {last_update}")
            
            return True
            
        except Exception as e:
            print(f"作品情報取得エラー: {str(e)}")
            # フォールバック：既存データベースから取得
            existing_info = self.get_work_info()
            if existing_info:
                self.novel_title = existing_info.get("title", f"作品ID_{self.work_id}")
                self.author_name = existing_info.get("author", "不明")
                if not self.end_chapter:
                    self.end_chapter = existing_info.get("total_chapters", 100)
                return True
            else:
                self.novel_title = f"作品ID_{self.work_id}"
                self.author_name = "不明"
                if not self.end_chapter:
                    self.end_chapter = 100
                return False
    
    def detect_max_chapter(self):
        """最大章数を自動検出"""
        print("最大章数を検出中...")
        
        test_chapters = [1000, 500, 200, 100, 50, 20, 10]
        max_found = 1
        
        for test_num in test_chapters:
            if self.chapter_exists(test_num):
                max_found = test_num
                break
        
        # 二分探索で正確な値を見つける
        low = max_found
        high = max_found * 2
        
        while self.chapter_exists(high):
            low = high
            high *= 2
            if high > 10000:
                break
        
        while low < high:
            mid = (low + high + 1) // 2
            if self.chapter_exists(mid):
                low = mid
            else:
                high = mid - 1
        
        print(f"最大章数検出完了: {low}章")
        return low
    
    def chapter_exists(self, chapter_num):
        """指定章が存在するかチェック"""
        try:
            url = urljoin(self.base_url, f"{chapter_num}/")
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            response = requests.head(url, headers=headers, timeout=10)
            return response.status_code == 200
        except:
            return False
    
    def load_progress(self):
        """進捗状況をロード"""
        if os.path.exists(self.work_progress_file):
            with open(self.work_progress_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {"completed": [], "failed": [], "download_sessions": []}
    
    def save_progress(self, completed, failed):
        """進捗状況を保存"""
        progress = self.load_progress()
        progress.update({
            "work_id": self.work_id,
            "novel_title": self.novel_title,
            "completed": completed,
            "failed": failed,
            "last_update": datetime.now().isoformat(),
            "total_chapters": self.end_chapter
        })
        
        # 今回のダウンロードセッション情報を記録
        current_session = {
            "session_date": datetime.now().isoformat(),
            "chapters_downloaded": len(set(completed) - set(progress.get("completed", []))),
            "total_chapters_at_time": self.end_chapter,
            "failed_chapters": failed
        }
        
        if "download_sessions" not in progress:
            progress["download_sessions"] = []
        progress["download_sessions"].append(current_session)
        
        with open(self.work_progress_file, 'w', encoding='utf-8') as f:
            json.dump(progress, f, ensure_ascii=False, indent=2)
    
    def check_for_updates(self):
        """更新チェック（新章・章数増加の検出）"""
        work_info = self.get_work_info()
        progress = self.load_progress()
        
        if not work_info:
            print("初回ダウンロードです")
            return True
        
        previous_total = work_info.get("total_chapters", 0)
        previous_completed = set(progress.get("completed", []))
        
        print(f"更新チェック:")
        print(f"  前回の総章数: {previous_total}章")
        print(f"  前回完了章数: {len(previous_completed)}章")
        print(f"  現在の総章数: {self.end_chapter}章")
        
        if self.end_chapter > previous_total:
            new_chapters = self.end_chapter - previous_total
            print(f"  🆕 新章発見: {new_chapters}章追加されています")
            return True
        elif len(previous_completed) < previous_total:
            incomplete = previous_total - len(previous_completed)
            print(f"  ⚠️  未完了章: {incomplete}章が未ダウンロードです")
            return True
        else:
            print("  ✅ 更新なし（全章ダウンロード済み）")
            if not self.force_update:
                print("強制更新するには --force オプションを使用してください")
                return False
            else:
                print("--force オプションにより強制実行します")
                return True
    
    def get_output_filename(self):
        """出力ファイル名を生成"""
        safe_title = re.sub(r'[<>:"/\\|?*]', '_', self.novel_title)
        timestamp = datetime.now().strftime('%Y%m%d')
        return os.path.join(self.output_dir, f"{self.work_id}_{safe_title}_{timestamp}.txt")
    
    def extract_chapter_content(self, url, chapter_num):
        """章の内容を抽出する"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'ja,en-US;q=0.9,en;q=0.8',
            }
            
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # タイトルの抽出
            title = None
            title_patterns = [
                soup.find('h1'),
                soup.find('h2'),
                soup.find('div', class_='novel_title'),
                soup.find('p', class_='novel_subtitle'),
            ]
            
            for pattern in title_patterns:
                if pattern and pattern.get_text(strip=True):
                    title = pattern.get_text(strip=True)
                    break
            
            if not title:
                page_title = soup.find('title')
                if page_title:
                    title_text = page_title.get_text()
                    if '小説家になろう' in title_text:
                        title = title_text.split('小説家になろう')[0].strip()
                    else:
                        title = title_text.strip()
                else:
                    title = f"第{chapter_num}話"
            
            # 本文の抽出
            content = None
            content_selectors = [
                'div.novel_view',
                'div#novel_honbun', 
                'div.p-novel__body',
                'div.novel_body',
                'div[id*="honbun"]',
                'div[class*="novel"]',
            ]
            
            for selector in content_selectors:
                element = soup.select_one(selector)
                if element:
                    content = element
                    break
            
            if not content:
                all_divs = soup.find_all('div')
                for div in all_divs:
                    div_text = div.get_text(strip=True)
                    if len(div_text) > 200 and re.search(r'[ひらがなカタカナ漢字]', div_text):
                        content = div
                        break
            
            if content:
                content_text = content.get_text(separator='\n', strip=True)
                
                lines = content_text.split('\n')
                cleaned_lines = []
                seen_lines = set()
                
                for line in lines:
                    line = line.strip()
                    if line and not self.is_noise_line(line) and line not in seen_lines:
                        cleaned_lines.append(line)
                        seen_lines.add(line)
                
                content_text = '\n\n'.join(cleaned_lines)
                return title, content_text
            else:
                return title, "本文の抽出に失敗しました"
                
        except requests.exceptions.RequestException as e:
            return f"第{chapter_num}話", f"HTTP取得エラー: {str(e)}"
        except Exception as e:
            return f"第{chapter_num}話", f"取得エラー: {str(e)}"
    
    def is_noise_line(self, line):
        """ノイズライン判定"""
        noise_patterns = [
            r'^(前へ|次へ|目次|ブックマーク)',
            r'^[0-9]+$',
            r'^(※|注意|警告)',
            r'(広告|AD|PR)',
            r'^(更新|投稿)',
            r'評価|感想|レビュー'
        ]
        
        for pattern in noise_patterns:
            if re.search(pattern, line):
                return True
        return False
    
    def initialize_output_file(self, output_file):
        """出力ファイルの初期化"""
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("===============================================\n")
            f.write(f"{self.novel_title}\n")
            f.write("===============================================\n\n")
            f.write("※ 本文は「小説家になろう」より取得\n")
            f.write(f"※ 作品ID: {self.work_id}\n")
            f.write(f"※ URL: {self.base_url}\n")
            f.write(f"※ 作者: {self.author_name}\n")
            f.write(f"※ 取得日: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"※ 章数: {self.end_chapter}章\n")
            f.write("※ 拡張版ダウンローダー使用（進捗管理・更新検知対応）\n\n")
    
    def append_chapter(self, output_file, chapter_num, title, content):
        """章をファイルに追記"""
        with open(output_file, 'a', encoding='utf-8') as f:
            f.write("===============================================\n")
            f.write(f"第{chapter_num}章 - {title}\n")
            f.write("===============================================\n\n")
            f.write(content)
            f.write("\n\n")
    
    def show_progress(self, current, total, failed_count):
        """進捗表示"""
        percentage = (current / total) * 100
        print(f"\r進捗: {current}/{total} ({percentage:.1f}%) | 失敗: {failed_count}", end='', flush=True)
    
    def download_all(self):
        """全章ダウンロード実行"""
        # 作品情報を取得
        if not self.get_novel_info():
            print("作品情報の取得に失敗しましたが、処理を続行します")
        
        # 更新チェック
        if not self.check_for_updates():
            print("ダウンロードをスキップします")
            return
        
        # 出力ファイル名を決定
        output_file = self.get_output_filename()
        
        print(f"\n小説ダウンロード開始: {self.novel_title}")
        print(f"作品ID: {self.work_id}")
        print(f"取得予定: 第{self.start_chapter}章～第{self.end_chapter}章")
        print(f"出力先: {output_file}")
        
        # 進捗をロード
        progress = self.load_progress()
        completed_chapters = set(progress.get("completed", []))
        failed_chapters = set(progress.get("failed", []))
        
        # 出力ファイルを初期化
        self.initialize_output_file(output_file)
        
        total_chapters = self.end_chapter - self.start_chapter + 1
        processed = 0
        new_downloads = 0
        
        for chapter_num in range(self.start_chapter, self.end_chapter + 1):
            # 強制更新でない場合、完了済み章はスキップ
            if not self.force_update and chapter_num in completed_chapters:
                processed += 1
                self.show_progress(processed, total_chapters, len(failed_chapters))
                continue
            
            chapter_url = urljoin(self.base_url, f"{chapter_num}/")
            title, content = self.extract_chapter_content(chapter_url, chapter_num)
            
            if "エラー" in content:
                failed_chapters.add(chapter_num)
                print(f"\n第{chapter_num}章の取得に失敗")
            else:
                self.append_chapter(output_file, chapter_num, title, content)
                completed_chapters.add(chapter_num)
                new_downloads += 1
                print(f"\n第{chapter_num}章完了: {title}")
            
            processed += 1
            self.show_progress(processed, total_chapters, len(failed_chapters))
            
            # 進捗を保存
            self.save_progress(list(completed_chapters), list(failed_chapters))
            
            # サイトに負荷をかけないよう待機
            time.sleep(2.5)
        
        print(f"\n\n処理完了!")
        print(f"作品名: {self.novel_title}")
        print(f"今回ダウンロード: {new_downloads}章")
        print(f"累計完了: {len(completed_chapters)}章")
        print(f"失敗: {len(failed_chapters)}章")
        print(f"出力ファイル: {output_file}")
        
        if failed_chapters:
            print(f"失敗した章: {sorted(failed_chapters)}")
        
        # 作品情報を更新
        self.update_work_info({
            "total_chapters": self.end_chapter,
            "completed_chapters": len(completed_chapters),
            "last_download_session": datetime.now().isoformat()
        })
    
    def show_status(self):
        """作品の状態を表示"""
        work_info = self.get_work_info()
        progress = self.load_progress()
        
        if not work_info:
            print(f"作品ID {self.work_id} の情報が見つかりません")
            return
        
        print(f"=== 作品状態: {work_info.get('title', self.work_id)} ===")
        print(f"作品ID: {self.work_id}")
        print(f"作者: {work_info.get('author', '不明')}")
        print(f"総章数: {work_info.get('total_chapters', 0)}章")
        print(f"完了章数: {len(progress.get('completed', []))}章")
        print(f"失敗章数: {len(progress.get('failed', []))}章")
        print(f"初回DL: {work_info.get('first_downloaded', '不明')}")
        print(f"最終DL: {work_info.get('last_download_session', '不明')}")
        
        sessions = progress.get('download_sessions', [])
        if sessions:
            print(f"\nダウンロード履歴:")
            for i, session in enumerate(sessions[-5:], 1):  # 最新5件
                print(f"  {i}. {session['session_date'][:10]} - {session['chapters_downloaded']}章取得")

def main():
    parser = argparse.ArgumentParser(description='小説家になろう 拡張版ダウンローダー')
    parser.add_argument('work_id', help='作品ID (例: n7069ds, n2627t, n5455cx)')
    parser.add_argument('--start', type=int, default=1, help='開始章 (デフォルト: 1)')
    parser.add_argument('--end', type=int, help='終了章 (未指定時は自動検出)')
    parser.add_argument('--output-dir', default='/home/hijiri/claude/claude/narou', help='出力ディレクトリ')
    parser.add_argument('--force', action='store_true', help='強制更新（既ダウンロード章も再取得）')
    parser.add_argument('--status', action='store_true', help='作品の状態を表示')
    
    args = parser.parse_args()
    
    # 出力ディレクトリを作成
    os.makedirs(args.output_dir, exist_ok=True)
    
    downloader = EnhancedNovelDownloader(
        work_id=args.work_id,
        output_dir=args.output_dir,
        start_chapter=args.start,
        end_chapter=args.end,
        force_update=args.force
    )
    
    if args.status:
        # 作品情報を取得して表示
        downloader.get_novel_info()
        downloader.show_status()
    else:
        downloader.download_all()

if __name__ == "__main__":
    main()