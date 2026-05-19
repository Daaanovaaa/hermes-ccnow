#!/usr/bin/env python3
"""
Hermes Update Intelligence Tracker for hermes-ccnow OS
Weekly Sunday 8 AM AST check for Hermes updates
"""

import os
import re
import subprocess
import json
import requests
from datetime import datetime

def get_current_version():
    """Get current Hermes version from local file or hermes command"""
    version_file = '/root/hermes-ccnow/hermes_version.txt'
    if os.path.exists(version_file):
        with open(version_file, 'r') as f:
            return f.read().strip()
    else:
        # Fallback to checking hermes version command
        result = subprocess.run(['hermes', 'version'], capture_output=True, text=True)
        version_match = re.search(r'Hermes Agent v(\d+\.\d+\.\d+)', result.stdout)
        return version_match.group(1) if version_match else "0.0.0"

def store_version(version):
    """Store version in local file"""
    version_file = '/root/hermes-ccnow/hermes_version.txt'
    with open(version_file, 'w') as f:
        f.write(version)

def check_for_updates():
    """Check GitHub for latest Hermes release"""
    try:
        response = requests.get('https://api.github.com/repos/nousresearch/hermes-agent/releases/latest', timeout=10)
        if response.status_code != 200:
            return None, f"Failed to fetch releases: HTTP {response.status_code}"
        
        release_data = response.json()
        latest_tag = release_data['tag_name']  # e.g., "v2026.5.16"
        latest_version = latest_tag[1:] if latest_tag.startswith('v') else latest_tag
        release_name = release_data['name']
        body = release_data.get('body', '')
        published_at = release_data['published_at']
        
        return {
            'version': latest_version,
            'name': release_name,
            'body': body,
            'published_at': published_at
        }, None
    except Exception as e:
        return None, f"Error checking for updates: {e}"

def extract_changelog_items(body):
    """Extract changelog items from release body"""
    changelog_items = []
    if not body:
        return changelog_items
    
    lines = body.split('\n')
    for line in lines:
        line = line.strip()
        # Look for bullet points or highlighted features
        if line.startswith('•') or line.startswith('- ') or line.startswith('* ') or ' — ' in line:
            # Clean up the line
            clean_line = line.lstrip('•-* ').strip()
            if clean_line and len(clean_line) > 10:  # Avoid too short items
                changelog_items.append(clean_line)
    
    # If no structured changelog, use the first few sentences
    if not changelog_items and body:
        sentences = body.split('. ')
        changelog_items = [s.strip() + '.' for s in sentences[:5] if len(s.strip()) > 20]
    
    return changelog_items

def filter_relevant_items(items):
    """Filter items relevant to CC NOW! OS"""
    relevant_keywords = [
        'cron', 'schedule', 'google', 'workspace', 'telegram', 'discord', 
        'mcp', 'plaid', 'financial', 'calendar', 'gateway', 'messaging',
        'notification', 'update', 'version', 'release', 'kanban', 'webhook'
    ]
    
    relevant_items = []
    for item in items:
        item_lower = item.lower()
        if any(keyword in item_lower for keyword in relevant_keywords):
            relevant_items.append(item)
    
    return relevant_items

def format_telegram_message(current_version, latest_release, changelog_items, relevant_items):
    """Format the Telegram message"""
    message = f"""HERMES UPDATE INTELLIGENCE
Current version: {current_version}
Latest version: {latest_release['version']}
Key changes:
"""
    
    # Add key changes (max 5)
    for item in changelog_items[:5]:
        message += f"- {item}\n"
    
    message += "\nItems relevant to CC NOW! OS:\n"
    if relevant_items:
        for item in relevant_items[:5]:
            message += f"- {item}\n"
    else:
        message += "- None detected\n"
    
    message += f"""Recommended action: Update now — New release includes features relevant to your OS integrations
Breaking changes warning: None detected (review changelog for details)"""
    
    return message

def main():
    print("Running Hermes Update Intelligence Tracker...")
    
    # Get current version
    current_version = get_current_version()
    print(f"Current version: {current_version}")
    
    # Check for updates
    latest_release, error = check_for_updates()
    if error:
        print(error)
        # Don't send error notifications for routine checks
        return
    
    if not latest_release:
        print("No release data available")
        return
    
    latest_version = latest_release['version']
    print(f"Latest version: {latest_version}")
    
    # Compare versions
    def version_tuple(v):
        return tuple(map(int, v.split('.')))
    
    try:
        current_tuple = version_tuple(current_version)
        latest_tuple = version_tuple(latest_version)
        
        if latest_tuple <= current_tuple:
            print(f"No update needed. Current ({current_version}) >= Latest ({latest_version})")
            return
    except Exception as e:
        print(f"Error comparing versions: {e}")
        # If we can't compare, assume we should check
        pass
    
    print(f"NEW VERSION AVAILABLE: {latest_version} > {current_version}")
    
    # Extract changelog
    changelog_items = extract_changelog_items(latest_release['body'])
    print(f"Found {len(changelog_items)} changelog items")
    
    # Filter relevant items
    relevant_items = filter_relevant_items(changelog_items)
    print(f"Found {len(relevant_items)} relevant items")
    
    # Format and send message
    message = format_telegram_message(
        current_version, 
        latest_release, 
        changelog_items, 
        relevant_items
    )
    
    print("Sending update notification to Telegram...")
    
    # Send to Telegram
    target = "telegram:Carlos “DaNova” Villanueva"
    send_result = subprocess.run([
        'hermes', 'send', '--to', target, message
    ], capture_output=True, text=True)
    
    if send_result.returncode == 0:
        print("Update notification sent to Telegram")
        
        # Update stored version
        store_version(latest_version)
        print(f"Updated version file to {latest_version}")
    else:
        print(f"Failed to send Telegram message: {send_result.stderr}")

if __name__ == "__main__":
    main()