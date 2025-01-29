import os
import json
import csv
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Iterator
from anthropic import Anthropic
import yaml
import re
from dotenv import load_dotenv
import time

def load_config() -> Dict:
    """Load and return the configuration."""
    config_path = Path(__file__).parent / "config.json"
    if not config_path.exists():
        raise FileNotFoundError("Config file not found")
    with open(config_path) as f:
        return json.load(f)

def load_translation_prompt() -> str:
    """Load the translation prompt from the prompt file."""
    prompt_path = Path(__file__).parent / "prompt.txt"
    if not prompt_path.exists():
        raise FileNotFoundError("Translation prompt file not found")
    return prompt_path.read_text()

def extract_yaml_and_content(markdown_content: str) -> tuple[Dict, str]:
    """Extract YAML frontmatter and content from markdown."""
    yaml_pattern = r"^---\s*\n(.*?)\n---\s*\n"
    match = re.match(yaml_pattern, markdown_content, re.DOTALL)
    
    if match:
        yaml_text = match.group(1)
        try:
            frontmatter = yaml.safe_load(yaml_text) or {}
            content = markdown_content[match.end():]
            return frontmatter, content
        except yaml.YAMLError:
            return {}, markdown_content
    return {}, markdown_content

def add_translation_metadata(frontmatter: Dict, target_lang: str) -> Dict:
    """Add translation metadata to frontmatter."""
    frontmatter['language'] = target_lang
    frontmatter['translation_status'] = 'translated'
    frontmatter['translation_date'] = datetime.now().strftime('%Y-%m-%d')
    return frontmatter

def get_pending_translations(status_file: Path, batch_size: int = None) -> Iterator[Dict]:
    """Get pending translations from status file."""
    if not status_file.exists():
        print("❌ Status file not found. Please run scan_files.py first.")
        return
    
    with open(status_file, 'r', newline='') as f:
        reader = csv.DictReader(f)
        pending = [row for row in reader if row['status'] == 'pending']
    
    if batch_size:
        pending = pending[:batch_size]
    
    for row in pending:
        yield row

def translate_and_save(source_path: Path, target_path: Path, target_lang: str, client: Anthropic) -> bool:
    """Translate a single file and save it immediately."""
    try:
        content = source_path.read_text()
        print(f"\n🔄 Translating: {source_path}")
        
        # Extract YAML and content
        frontmatter, markdown_content = extract_yaml_and_content(content)
        
        # Prepare content for translation
        content_to_translate = ""
        if 'title' in frontmatter:
            content_to_translate = f"{frontmatter['title']}\n\n"
        content_to_translate += markdown_content
        
        prompt = load_translation_prompt()
        messages = [
            {
                "role": "user",
                "content": f"{prompt}\n\nTarget language: {target_lang}\n\nMarkdown content to translate:\n\n{content_to_translate}"
            }
        ]
        
        response = client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=4096,
            messages=messages
        )
        
        translated_content = response.content[0].text.strip()
        
        # If there was a title, extract it from the first line
        if 'title' in frontmatter:
            lines = translated_content.split('\n\n', 1)
            if len(lines) == 2:
                frontmatter['title'] = lines[0].strip()
                translated_content = lines[1].strip()
        
        # Add translation metadata to frontmatter
        updated_frontmatter = add_translation_metadata(frontmatter, target_lang)
        
        # Combine updated frontmatter with translated content
        final_content = "---\n" + yaml.dump(updated_frontmatter, allow_unicode=True, sort_keys=False) + "---\n\n" + translated_content
        
        # Ensure target directory exists
        target_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save the translated file
        target_path.write_text(final_content)
        print(f"✅ Successfully saved to: {target_path}")
        return True
        
    except KeyboardInterrupt:
        print("\n⚠️  Translation interrupted by user")
        raise
    except Exception as e:
        print(f"❌ Error translating {source_path}: {str(e)}")
        return False

def update_status_row(status_file: Path, row: Dict, new_status: str):
    """Update a single row in the status CSV file."""
    rows = []
    with open(status_file, 'r', newline='') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        for r in reader:
            if r['source_file'] == row['source_file'] and r['language'] == row['language']:
                r['status'] = new_status
                r['last_updated'] = datetime.now().strftime('%Y-%m-%d')
            rows.append(r)
    
    with open(status_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

def main():
    # Load environment variables from .env file
    load_dotenv()
    
    print(f"\n🚀 Starting translation process at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        if not client.api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in .env file")
        
        # Load configuration
        config = load_config()
        source_root = Path(config["source_path"])
        output_root = Path(config["output_path"])
        batch_size = config.get("batch_size", None)
        
        # Status file path
        status_file = Path(__file__).parent / "translation_status.csv"
        
        if not status_file.exists():
            print("❌ Status file not found. Please run scan_files.py first.")
            return
        
        print(f"\n📊 Reading from status file: {status_file}")
        print(f"📂 Source path: {source_root}")
        print(f"💾 Output path: {output_root}")
        
        stats = {"translated": 0, "failed": 0, "total": 0}
        start_time = time.time()
        
        try:
            for entry in get_pending_translations(status_file, batch_size):
                stats["total"] += 1
                source_path = source_root / entry['source_file']
                target_path = output_root / entry['language'] / entry['source_file']
                
                if translate_and_save(source_path, target_path, entry['language'], client):
                    stats["translated"] += 1
                    update_status_row(status_file, entry, "translated")
                else:
                    stats["failed"] += 1
                    update_status_row(status_file, entry, "failed")
                
                # Print progress
                elapsed = time.time() - start_time
                print(f"\n{'='*50}")
                print(f"Progress:")
                print(f"{'='*50}")
                print(f"Files processed: {stats['translated'] + stats['failed']}/{stats['total']}")
                print(f"Successfully translated: {stats['translated']}")
                print(f"Failed: {stats['failed']}")
                print(f"Elapsed time: {elapsed:.1f}s")
                print(f"{'='*50}\n")
                
        except KeyboardInterrupt:
            print("\n⚠️  Translation process interrupted by user")
            print(f"Progress saved in status file. You can continue later.")
            return
            
        print(f"\n✨ Translation process completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        raise

if __name__ == "__main__":
    main() 