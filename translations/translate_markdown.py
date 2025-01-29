import os
import json
from pathlib import Path
from anthropic import Anthropic
from typing import List, Dict, Set
from dotenv import load_dotenv
from datetime import datetime
import time
import re
import yaml

def load_translation_prompt() -> str:
    """Load the translation prompt from the prompt file."""
    prompt_path = Path(__file__).parent / "prompt.txt"
    if not prompt_path.exists():
        raise FileNotFoundError("Translation prompt file not found")
    return prompt_path.read_text()

def load_config() -> Dict:
    """Load and return the configuration."""
    config_path = Path(__file__).parent / "config.json"
    if not config_path.exists():
        raise FileNotFoundError("Config file not found")
    with open(config_path) as f:
        return json.load(f)

def get_target_languages() -> List[str]:
    """Get list of target languages from config."""
    return load_config()["target_languages"]

def create_target_path(source_path: Path, source_root: Path, output_root: Path, target_lang: str) -> Path:
    """Create the equivalent path in the target language directory."""
    rel_path = source_path.relative_to(source_root)
    target_path = output_root / target_lang / rel_path
    target_path.parent.mkdir(parents=True, exist_ok=True)
    return target_path

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

def translate_and_save(source_path: Path, target_path: Path, target_lang: str, client: Anthropic) -> bool:
    """Translate a single file and save it immediately."""
    try:
        content = source_path.read_text()
        print(f"\n🔄 Translating: {source_path}")
        
        # Extract YAML and content
        frontmatter, markdown_content = extract_yaml_and_content(content)
        
        prompt = load_translation_prompt()
        messages = [
            {
                "role": "user",
                "content": f"{prompt}\n\nTarget language: {target_lang}\n\nMarkdown content to translate:\n\n{markdown_content}"
            }
        ]
        
        response = client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=4096,
            messages=messages
        )
        
        translated_content = response.content[0].text
        
        # Add translation metadata to frontmatter
        updated_frontmatter = add_translation_metadata(frontmatter, target_lang)
        
        # Combine updated frontmatter with translated content
        final_content = "---\n" + yaml.dump(updated_frontmatter, allow_unicode=True, sort_keys=False) + "---\n\n" + translated_content
        
        target_path.write_text(final_content)
        print(f"✅ Successfully saved to: {target_path}")
        return True
        
    except KeyboardInterrupt:
        print("\n⚠️  Translation interrupted by user")
        raise
    except Exception as e:
        print(f"❌ Error translating {source_path}: {str(e)}")
        return False

class TranslationStats:
    def __init__(self):
        self.total_files = 0
        self.translated_files = 0
        self.skipped_files = 0
        self.failed_files = 0
        self.start_time = time.time()
        self.current_file = ""
        
    def print_progress(self, target_lang: str):
        elapsed = time.time() - self.start_time
        remaining_files = self.total_files - (self.translated_files + self.skipped_files + self.failed_files)
        
        if self.translated_files > 0:
            avg_time = elapsed / self.translated_files
            eta = avg_time * remaining_files
        else:
            eta = 0
            
        print(f"\n{'='*50}")
        print(f"Progress for {target_lang}:")
        print(f"{'='*50}")
        print(f"Total files found: {self.total_files}")
        print(f"Files translated: {self.translated_files}")
        print(f"Files skipped: {self.skipped_files}")
        print(f"Files failed: {self.failed_files}")
        print(f"Files remaining: {remaining_files}")
        print(f"Elapsed time: {elapsed:.1f}s")
        if eta > 0:
            print(f"Estimated time remaining: {eta:.1f}s")
        if self.current_file:
            print(f"\nLast processed: {self.current_file}")
        print(f"{'='*50}\n")

def get_markdown_files(source_root: Path, source_dirs: List[str]) -> List[Path]:
    """Get all markdown files to process."""
    files = []
    for dir_name in source_dirs:
        dir_path = source_root / dir_name
        if dir_path.exists():
            files.extend([f for f in dir_path.rglob("*") if f.suffix.lower() in ['.md', '.markdown']])
    return sorted(files)

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
        source_dirs = config["source_directories"]
        target_languages = config["target_languages"]
        
        if not source_root.exists():
            raise FileNotFoundError(f"Source path not found: {source_root}")
            
        # Create output directory if it doesn't exist
        output_root.mkdir(parents=True, exist_ok=True)
        
        # Get all markdown files
        markdown_files = get_markdown_files(source_root, source_dirs)
        
        # Initialize stats
        stats = TranslationStats()
        stats.total_files = len(markdown_files)
        
        print(f"\n📁 Found {stats.total_files} markdown files to process")
        print(f"📂 Source path: {source_root}")
        print(f"💾 Output path: {output_root}")
        print(f"🌐 Target languages: {', '.join(target_languages)}")
        
        try:
            for target_lang in target_languages:
                print(f"\n🔍 Processing translations for {target_lang}")
                
                for source_path in markdown_files:
                    stats.current_file = str(source_path.relative_to(source_root))
                    target_path = create_target_path(source_path, source_root, output_root, target_lang)
                    
                    if target_path.exists():
                        print(f"⏭️  Skipping existing translation: {target_path}")
                        stats.skipped_files += 1
                    else:
                        if translate_and_save(source_path, target_path, target_lang, client):
                            stats.translated_files += 1
                        else:
                            stats.failed_files += 1
                    
                    stats.print_progress(target_lang)
                    
        except KeyboardInterrupt:
            print("\n⚠️  Translation process interrupted by user")
            print(f"Progress saved. You can restart the script to continue from where you left off.")
            return
            
        print(f"\n✨ Translation process completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        raise

if __name__ == "__main__":
    main() 