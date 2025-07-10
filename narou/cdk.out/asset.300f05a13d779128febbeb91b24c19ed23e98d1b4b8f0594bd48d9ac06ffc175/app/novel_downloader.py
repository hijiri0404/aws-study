"""
小説ダウンローダーコアクラス
ECS環境用に簡略化されたバージョン
"""

import requests
import time
import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import logging

logger = logging.getLogger(__name__)

class NovelDownloader:
    """小説ダウンローダークラス"""
    
    def __init__(self, delay=1.0):
        self.delay = delay
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def download_novel(self, work_url):
        """小説をダウンロード"""
        logger.info(f"Starting download from {work_url}")
        
        # 作品情報を取得
        work_info = self._get_work_info(work_url)
        
        # 各章をダウンロード
        chapters = []
        for i in range(1, work_info['total_chapters'] + 1):
            chapter_url = f"{work_url}{i}/"
            chapter_content = self._download_chapter(chapter_url, i)
            chapters.append(chapter_content)
            
            # レート制限
            time.sleep(self.delay)
        
        # ファイルに保存
        output_file = f"/tmp/{work_info['title']}.txt"
        self._save_to_file(chapters, work_info, output_file)
        
        return {
            'title': work_info['title'],
            'total_chapters': work_info['total_chapters'],
            'output_file': output_file
        }
    
    def _get_work_info(self, work_url):
        """作品情報を取得"""
        response = self.session.get(work_url)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # タイトル取得
        title_element = soup.find('p', class_='novel_title')
        title = title_element.get_text(strip=True) if title_element else "Unknown Title"
        
        # 章数を検出
        total_chapters = self._detect_total_chapters(work_url, soup)
        
        return {
            'title': title,
            'total_chapters': total_chapters
        }
    
    def _detect_total_chapters(self, work_url, soup):
        """総章数を検出"""
        # 目次から章数を検出
        index_links = soup.find_all('a', href=re.compile(r'/\d+/$'))
        
        if index_links:
            chapter_numbers = []
            for link in index_links:
                href = link.get('href', '')
                match = re.search(r'/(\d+)/$', href)
                if match:
                    chapter_numbers.append(int(match.group(1)))
            
            if chapter_numbers:
                max_chapter = max(chapter_numbers)
                
                # 100章ちょうどの場合は続きがある可能性があるため詳細検出
                if max_chapter == 100:
                    return self._binary_search_max_chapter(work_url)
                
                return max_chapter
        
        # フォールバック: 1章から順番にチェック
        return self._binary_search_max_chapter(work_url)
    
    def _binary_search_max_chapter(self, work_url):
        """二分探索で最大章数を検出"""
        left, right = 1, 2000  # 最大2000章まで想定
        max_valid = 1
        
        while left <= right:
            mid = (left + right) // 2
            chapter_url = f"{work_url}{mid}/"
            
            try:
                response = self.session.get(chapter_url)
                if response.status_code == 200:
                    max_valid = mid
                    left = mid + 1
                else:
                    right = mid - 1
            except:
                right = mid - 1
            
            time.sleep(0.5)  # レート制限
        
        return max_valid
    
    def _download_chapter(self, chapter_url, chapter_num):
        """1章分をダウンロード"""
        logger.info(f"Downloading chapter {chapter_num}")
        
        response = self.session.get(chapter_url)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # 章タイトル
        title_element = soup.find('p', class_='novel_subtitle')
        title = title_element.get_text(strip=True) if title_element else f"第{chapter_num}章"
        
        # 本文
        content_element = soup.find('div', id='novel_honbun')
        content = ""
        
        if content_element:
            # 段落ごとに処理
            for p in content_element.find_all('p'):
                content += p.get_text() + "\n"
        
        return {
            'chapter_num': chapter_num,
            'title': title,
            'content': content.strip()
        }
    
    def _save_to_file(self, chapters, work_info, output_file):
        """ファイルに保存"""
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"タイトル: {work_info['title']}\n")
            f.write(f"総章数: {work_info['total_chapters']}\n")
            f.write("=" * 50 + "\n\n")
            
            for chapter in chapters:
                f.write(f"第{chapter['chapter_num']}章: {chapter['title']}\n")
                f.write("-" * 30 + "\n")
                f.write(chapter['content'])
                f.write("\n\n")
        
        logger.info(f"Novel saved to {output_file}")