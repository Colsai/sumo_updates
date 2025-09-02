#!/usr/bin/env python3
"""
View and manage email archives
"""

import os
import json
import sys
from datetime import datetime
from typing import List, Dict

def list_archives():
    """List all archived emails"""
    archives_path = os.path.join(os.path.dirname(__file__), 'archives')
    
    if not os.path.exists(archives_path):
        print('No archives folder found. Generate an email first to create archives.')
        return
    
    json_files = [f for f in os.listdir(archives_path) if f.endswith('.json')]
    
    if not json_files:
        print('No email archives found.')
        return
    
    print('''
    Email Archives Viewer
         (^_^)
    ''')
    print(f'Found {len(json_files)} archived emails:')
    print('=' * 60)
    
    # Sort by filename (which includes timestamp)
    json_files.sort(reverse=True)  # Most recent first
    
    for i, filename in enumerate(json_files, 1):
        try:
            filepath = os.path.join(archives_path, filename)
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            timestamp = data.get('timestamp', 'Unknown')
            subject = data.get('subject', 'No Subject')
            article_count = data.get('article_count', 0)
            
            # Parse timestamp for better display
            try:
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                display_time = dt.strftime('%Y-%m-%d %H:%M')
            except:
                display_time = timestamp[:19] if len(timestamp) > 19 else timestamp
            
            print(f'{i:2d}. {display_time} - {subject}')
            print(f'    {article_count} articles | Files: {filename[:-5]}.json/.html')
            print()
            
        except Exception as e:
            print(f'{i:2d}. {filename} - Error reading file: {e}')

def view_archive(archive_number: int):
    """View a specific archive by number"""
    archives_path = os.path.join(os.path.dirname(__file__), 'archives')
    json_files = [f for f in os.listdir(archives_path) if f.endswith('.json')]
    json_files.sort(reverse=True)
    
    if archive_number < 1 or archive_number > len(json_files):
        print(f'Invalid archive number. Please choose 1-{len(json_files)}')
        return
    
    filename = json_files[archive_number - 1]
    filepath = os.path.join(archives_path, filename)
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print('=' * 60)
        print(f"ARCHIVE: {filename}")
        print('=' * 60)
        print(f"Timestamp: {data.get('timestamp', 'Unknown')}")
        print(f"Subject: {data.get('subject', 'No Subject')}")
        print(f"Recipient: {data.get('recipient', 'Unknown')}")
        print(f"Articles: {data.get('article_count', 0)}")
        print()
        print("Introduction:")
        print(f"  {data.get('intro', 'No introduction')}")
        print()
        print("Articles:")
        
        articles = data.get('articles', [])
        for i, article in enumerate(articles, 1):
            print(f"  {i}. [{article.get('source', 'Unknown')}] {article.get('title', 'No title')}")
            if article.get('summary'):
                print(f"     Summary: {article['summary']}")
            if article.get('url'):
                print(f"     URL: {article['url']}")
            print()
        
        html_file = filepath.replace('.json', '.html')
        if os.path.exists(html_file):
            print(f"HTML Version: {html_file}")
            print("  (Open this file in your browser to see the full email)")
    
    except Exception as e:
        print(f'Error reading archive: {e}')

def cleanup_old_archives(days: int = 30):
    """Remove archives older than specified days"""
    archives_path = os.path.join(os.path.dirname(__file__), 'archives')
    
    if not os.path.exists(archives_path):
        print('No archives folder found.')
        return
    
    cutoff = datetime.now().timestamp() - (days * 24 * 60 * 60)
    deleted_count = 0
    
    for filename in os.listdir(archives_path):
        filepath = os.path.join(archives_path, filename)
        if os.path.isfile(filepath):
            if os.path.getmtime(filepath) < cutoff:
                try:
                    os.remove(filepath)
                    deleted_count += 1
                    print(f'Deleted: {filename}')
                except Exception as e:
                    print(f'Error deleting {filename}: {e}')
    
    print(f'\nCleanup complete. Deleted {deleted_count} old archive files.')

def show_help():
    print('''
    Email Archives Manager
           (?)
    
Usage:
  python view_archives.py                 - List all archives
  python view_archives.py <number>        - View specific archive
  python view_archives.py cleanup [days]  - Clean archives older than N days (default: 30)
  python view_archives.py help            - Show this help

Examples:
  python view_archives.py 1              - View the most recent archive
  python view_archives.py cleanup 7      - Delete archives older than 7 days
''')

if __name__ == "__main__":
    if len(sys.argv) == 1:
        # No arguments - list all archives
        list_archives()
    elif len(sys.argv) == 2:
        if sys.argv[1] == 'help':
            show_help()
        elif sys.argv[1] == 'cleanup':
            cleanup_old_archives()
        elif sys.argv[1].isdigit():
            view_archive(int(sys.argv[1]))
        else:
            print(f"Unknown command: {sys.argv[1]}")
            show_help()
    elif len(sys.argv) == 3 and sys.argv[1] == 'cleanup':
        if sys.argv[2].isdigit():
            cleanup_old_archives(int(sys.argv[2]))
        else:
            print("Cleanup days must be a number")
    else:
        show_help()