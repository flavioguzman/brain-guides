import os
import json
import csv
from pathlib import Path
from datetime import datetime
from typing import List, Dict
import yaml
import re

def load_config() -> Dict:
    """Load and return the configuration."""
    config_path = Path(__file__).parent / "config.json"
    if not config_path.exists():
        raise FileNotFoundError("Config file not found")
    with open(config_path) as f:
        return json.load(f)

def extract_yaml_frontmatter(file_path: Path) -> Dict:
    """Extract YAML frontmatter from a markdown file."""
    content = file_path.read_text()
    yaml_pattern = r"^---\s*\n(.*?)\n---\s*\n"
    match = re.match(yaml_pattern, content, re.DOTALL)
    
    if match:
        try:
            return yaml.safe_load(match.group(1)) or {}
        except yaml.YAMLError:
            return {}
    return {}

def get_markdown_files(source_root: Path, source_dirs: List[str]) -> List[Path]:
    """Get all markdown files to process."""
    files = []
    for dir_name in source_dirs:
        dir_path = source_root / dir_name
        if dir_path.exists():
            files.extend([f for f in dir_path.rglob("*") if f.suffix.lower() in ['.md', '.markdown']])
    return sorted(files)

def get_translation_status(source_path: Path, target_path: Path) -> str:
    """Get translation status for a file."""
    if not target_path.exists():
        return 'pending'
    
    target_yaml = extract_yaml_frontmatter(target_path)
    return target_yaml.get('translation_status', 'unknown')

def update_status_csv(status_file: Path, source_root: Path, output_root: Path, markdown_files: List[Path], target_languages: List[str]):
    """Update the CSV status file."""
    # Read existing entries to preserve manual updates
    existing_entries = {}
    if status_file.exists():
        with open(status_file, 'r', newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                key = (row['source_file'], row['language'])
                existing_entries[key] = row

    # Prepare new entries
    fieldnames = ['source_file', 'language', 'status', 'last_updated', 'title']
    rows = []
    
    for source_path in markdown_files:
        rel_path = source_path.relative_to(source_root)
        frontmatter = extract_yaml_frontmatter(source_path)
        title = frontmatter.get('title', '')
        
        for lang in target_languages:
            key = (str(rel_path), lang)
            target_path = output_root / lang / rel_path
            
            if key in existing_entries:
                # Preserve existing entry but update status if file exists
                entry = existing_entries[key]
                current_status = get_translation_status(source_path, target_path)
                if current_status != 'pending':
                    entry['status'] = current_status
                    entry['last_updated'] = datetime.now().strftime('%Y-%m-%d')
            else:
                # Create new entry
                entry = {
                    'source_file': str(rel_path),
                    'language': lang,
                    'status': get_translation_status(source_path, target_path),
                    'last_updated': datetime.now().strftime('%Y-%m-%d'),
                    'title': title
                }
            
            rows.append(entry)
    
    # Write updated CSV
    rows.sort(key=lambda x: (x['source_file'], x['language']))
    with open(status_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

def main():
    print(f"\n🔍 Starting file scan at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Load configuration
        config = load_config()
        source_root = Path(config["source_path"])
        output_root = Path(config["output_path"])
        source_dirs = config["source_directories"]
        target_languages = config["target_languages"]
        
        if not source_root.exists():
            raise FileNotFoundError(f"Source path not found: {source_root}")
        
        # Get all markdown files
        markdown_files = get_markdown_files(source_root, source_dirs)
        
        # Status file path
        status_file = Path(__file__).parent / "translation_status.csv"
        
        print(f"\n📁 Found {len(markdown_files)} markdown files to process")
        print(f"📂 Source path: {source_root}")
        print(f"💾 Output path: {output_root}")
        print(f"📊 Status file: {status_file}")
        print(f"🌐 Target languages: {', '.join(target_languages)}")
        
        # Update status file
        update_status_csv(status_file, source_root, output_root, markdown_files, target_languages)
        
        print(f"\n✨ Status file updated at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        raise

if __name__ == "__main__":
    main() 