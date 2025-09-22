#!/usr/bin/env python3
"""
Higgsfield AI Video Downloader
Downloads videos from scraped data organized in folder structure
"""

import os
import json
import csv
import requests
import logging
from datetime import datetime
from urllib.parse import urlparse, urljoin
import time
from pathlib import Path

class HiggsfieldVideoDownloader:
    def __init__(self):
        self.download_folder = "downloaded_videos"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('video_downloader.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        # Create main download folder
        os.makedirs(self.download_folder, exist_ok=True)

    def get_category_folders(self):
        """Get all category folders in the current directory"""
        category_folders = []
        current_dir = os.getcwd()
        
        for item in os.listdir(current_dir):
            item_path = os.path.join(current_dir, item)
            if os.path.isdir(item_path) and item != self.download_folder:
                # Check if it has metadata.json (indicating it's a category folder)
                metadata_path = os.path.join(item_path, "metadata.json")
                if os.path.exists(metadata_path):
                    category_folders.append(item_path)
        
        return category_folders

    def find_video_files(self, category_folder):
        """Find all JSON and CSV files in subcategory folders"""
        video_files = []
        
        for root, dirs, files in os.walk(category_folder):
            for file in files:
                if file.endswith('.json') and file != 'metadata.json':
                    file_path = os.path.join(root, file)
                    video_files.append(file_path)
        
        return video_files

    def load_videos_from_json(self, json_file):
        """Load video data from JSON file"""
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            return data.get('videos', [])
            
        except Exception as e:
            self.logger.error(f"Error loading JSON file {json_file}: {e}")
            return []

    def get_file_extension(self, url):
        """Get file extension from URL"""
        parsed = urlparse(url)
        path = parsed.path
        
        if path.endswith('.mp4'):
            return '.mp4'
        elif path.endswith('.webm'):
            return '.webm'
        elif path.endswith('.mov'):
            return '.mov'
        else:
            return '.mp4'  # Default to mp4

    def sanitize_filename(self, filename):
        """Sanitize filename for filesystem"""
        import re
        # Remove or replace invalid characters
        sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
        sanitized = re.sub(r'\s+', ' ', sanitized).strip()
        return sanitized[:100]  # Limit length

    def download_video(self, video_url, save_path):
        """Download a single video"""
        try:
            self.logger.info(f"Downloading: {video_url}")
            
            response = self.session.get(video_url, stream=True, timeout=30)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded_size = 0
            
            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded_size += len(chunk)
                        
                        # Progress logging
                        if total_size > 0:
                            progress = (downloaded_size / total_size) * 100
                            if downloaded_size % (1024 * 1024) == 0:  # Log every MB
                                self.logger.info(f"Progress: {progress:.1f}%")
            
            self.logger.info(f"✅ Downloaded: {os.path.basename(save_path)}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to download {video_url}: {e}")
            return False

    def download_category_videos(self, category_folder):
        """Download all videos from a category folder"""
        try:
            category_name = os.path.basename(category_folder)
            self.logger.info(f"Processing category: {category_name}")
            
            # Find all video files
            video_files = self.find_video_files(category_folder)
            
            if not video_files:
                self.logger.warning(f"No video files found in {category_name}")
                return
            
            total_downloaded = 0
            total_failed = 0
            
            for json_file in video_files:
                try:
                    # Get subcategory folder path
                    subcategory_folder = os.path.dirname(json_file)
                    subcategory_name = os.path.basename(subcategory_folder)
                    
                    # Create videos folder within the subcategory
                    videos_folder = os.path.join(subcategory_folder, "videos")
                    os.makedirs(videos_folder, exist_ok=True)
                    
                    # Load videos from JSON
                    with open(json_file, 'r', encoding='utf-8') as f:
                        videos_data = json.load(f)
                    
                    # If it's a list, use it directly, otherwise extract 'videos' key
                    if isinstance(videos_data, list):
                        videos = videos_data
                    else:
                        videos = videos_data.get('videos', [])
                    
                    self.logger.info(f"Found {len(videos)} videos in {subcategory_name}")
                    
                    # Track which videos were updated with local paths
                    updated_videos = []
                    
                    for i, video in enumerate(videos):
                        try:
                            video_url = video.get('video_url', '')
                            prompt = video.get('prompt', f'video_{i+1}')
                            
                            if not video_url:
                                updated_videos.append(video)  # Keep videos without URLs
                                continue
                            
                            # Create filename based on video URL
                            video_id = os.path.basename(urlparse(video_url).path).split('.')[0]
                            extension = self.get_file_extension(video_url)
                            filename = f"{video_id}{extension}"
                            
                            # Full path to save the video
                            save_path = os.path.join(videos_folder, filename)
                            
                            # Skip if already exists but still update JSON
                            if os.path.exists(save_path):
                                self.logger.info(f"⏭️  Skipping existing: {filename}")
                                # Add local path info to video object
                                video['local_file_path'] = save_path
                                video['filename'] = filename
                                updated_videos.append(video)
                                continue
                            
                            # Download video
                            if self.download_video(video_url, save_path):
                                total_downloaded += 1
                                # Add local path info to video object
                                video['local_file_path'] = save_path
                                video['filename'] = filename
                            else:
                                total_failed += 1
                            
                            updated_videos.append(video)
                            
                            # Small delay between downloads
                            time.sleep(1)
                            
                        except Exception as e:
                            self.logger.error(f"Error processing video {i+1}: {e}")
                            updated_videos.append(video)  # Keep original entry even if download fails
                            total_failed += 1
                            continue
                    
                    # Update the JSON file with local paths
                    if isinstance(videos_data, list):
                        updated_json_data = updated_videos
                    else:
                        videos_data['videos'] = updated_videos
                        updated_json_data = videos_data
                    
                    with open(json_file, 'w', encoding='utf-8') as f:
                        json.dump(updated_json_data, f, indent=2, ensure_ascii=False)
                    
                    self.logger.info(f"✅ Updated {json_file} with local file paths")
                    
                except Exception as e:
                    self.logger.error(f"Error processing file {json_file}: {e}")
                    continue
            
            self.logger.info(f"Category {category_name} completed: {total_downloaded} downloaded, {total_failed} failed")
            
        except Exception as e:
            self.logger.error(f"Error processing category {category_folder}: {e}")

    def download_all_videos(self):
        """Download videos from all categories"""
        try:
            self.logger.info("Starting video download process...")
            
            # Get all category folders
            category_folders = self.get_category_folders()
            
            if not category_folders:
                self.logger.warning("No category folders found")
                return False
            
            self.logger.info(f"Found {len(category_folders)} categories to process")
            
            for category_folder in category_folders:
                try:
                    self.download_category_videos(category_folder)
                except Exception as e:
                    self.logger.error(f"Error processing category folder {category_folder}: {e}")
                    continue
            
            self.logger.info("✅ All downloads completed!")
            return True
            
        except Exception as e:
            self.logger.error(f"Error in download process: {e}")
            return False

    def download_specific_category(self, category_name):
        """Download videos from a specific category"""
        try:
            category_folder = os.path.join(os.getcwd(), category_name)
            
            if not os.path.exists(category_folder):
                self.logger.error(f"Category folder not found: {category_name}")
                return False
            
            self.download_category_videos(category_folder)
            return True
            
        except Exception as e:
            self.logger.error(f"Error downloading category {category_name}: {e}")
            return False

    def get_download_stats(self):
        """Get statistics about downloaded videos"""
        try:
            stats = {}
            
            if not os.path.exists(self.download_folder):
                return stats
            
            for category in os.listdir(self.download_folder):
                category_path = os.path.join(self.download_folder, category)
                if os.path.isdir(category_path):
                    video_count = 0
                    total_size = 0
                    
                    for root, dirs, files in os.walk(category_path):
                        for file in files:
                            if file.endswith(('.mp4', '.webm', '.mov')):
                                file_path = os.path.join(root, file)
                                video_count += 1
                                total_size += os.path.getsize(file_path)
                    
                    stats[category] = {
                        'video_count': video_count,
                        'total_size_mb': round(total_size / (1024 * 1024), 2)
                    }
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Error getting download stats: {e}")
            return {}

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Download Higgsfield AI videos')
    parser.add_argument('--category', help='Download specific category only')
    parser.add_argument('--stats', action='store_true', help='Show download statistics')
    parser.add_argument('--interactive', action='store_true', help='Interactive mode for category selection')
    
    args = parser.parse_args()
    
    downloader = HiggsfieldVideoDownloader()
    
    if args.stats:
        stats = downloader.get_download_stats()
        print("\n📊 Download Statistics:")
        for category, data in stats.items():
            print(f"  {category}: {data['video_count']} videos, {data['total_size_mb']} MB")
        return
    
    if args.interactive:
        # List available categories
        categories = downloader.get_category_folders()
        if not categories:
            print("❌ No categories with metadata.json found!")
            return
        
        print("\n📂 Available categories:")
        print("  0. All categories (process consecutively)")
        for i, category in enumerate(categories, 1):
            print(f"  {i}. {os.path.basename(category)}")
        
        # Get category choice
        try:
            choice = int(input(f"\nSelect category (0-{len(categories)}): ").strip())
            if choice == 0:
                # Process all categories consecutively
                print("🔄 Processing all categories consecutively...")
                success = downloader.download_all_videos()
            elif 1 <= choice <= len(categories):
                selected_category = categories[choice - 1]
                category_name = os.path.basename(selected_category)
                success = downloader.download_category_videos(selected_category)
            else:
                print("❌ Invalid category selection")
                return
        except ValueError:
            print("❌ Please enter a valid number")
            return
    elif args.category:
        success = downloader.download_specific_category(args.category)
    else:
        success = downloader.download_all_videos()
    
    if success:
        print("✅ Download process completed!")
    else:
        print("❌ Download process failed!")

if __name__ == "__main__":
    main()