import os
import json
import yaml
from pathlib import Path
from typing import Dict, List, Optional

class MarkdownFile:
    def __init__(self, path: Path):
        self.path = path
        self.front_matter: Optional[Dict] = None
        self.content: str = ""
        self._parse_file()
    
    def _parse_file(self):
        """Parse the markdown file to separate front matter and content."""
        with open(self.path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check if file has YAML front matter
        if content.startswith('---'):
            # Split on the second '---' to separate front matter and content
            parts = content.split('---', 2)
            if len(parts) >= 3:
                try:
                    self.front_matter = yaml.safe_load(parts[1])
                    self.content = parts[2].strip()
                except yaml.YAMLError:
                    print(f"Error parsing YAML front matter in {self.path}")
                    self.content = content
            else:
                self.content = content
        else:
            self.content = content
    
    def is_section(self) -> bool:
        """Check if the file is a section type."""
        if not self.front_matter or 'type' not in self.front_matter:
            return False
        
        file_type = self.front_matter['type']
        # Handle both string and list type values
        if isinstance(file_type, list):
            return 'section' in file_type
        return file_type == 'section'

def get_markdown_files(directory: Path) -> List[MarkdownFile]:
    """Recursively get all markdown files in directory and its subdirectories."""
    markdown_files = []
    for file_path in directory.rglob('*.md'):
        markdown_file = MarkdownFile(file_path)
        # Only include files with valid front matter that are sections
        if markdown_file.front_matter and markdown_file.is_section():
            markdown_files.append(markdown_file)
    return markdown_files

def sort_markdown_files(files: List[MarkdownFile]) -> List[MarkdownFile]:
    """Sort markdown files based on the order key in front matter."""
    return sorted(files, key=lambda x: x.front_matter.get('order', float('inf')))

def group_by_code_and_language(files: List[MarkdownFile]) -> Dict[str, Dict[Path, List[MarkdownFile]]]:
    """Group files by their code and language combination, and by directory."""
    groups = {}
    for file in files:
        if not file.front_matter:
            continue
        
        code = file.front_matter.get('code')
        language = file.front_matter.get('language', 'en')
        
        if code:
            key = f"{code}_{language}" if language != 'en' else code
            # Get the parent directory of where the markdown files are found
            directory = file.path.parent.parent
            
            if key not in groups:
                groups[key] = {}
            if directory not in groups[key]:
                groups[key][directory] = []
            
            groups[key][directory].append(file)
    
    return groups

def get_references_text(language: str, translations: Dict) -> str:
    """Get the references text in the appropriate language."""
    references = translations.get('references', {})
    return references.get(language, references.get('en', 'References'))

def create_output_front_matter(files: List[MarkdownFile], language: str) -> str:
    """Create YAML front matter for the output file."""
    if not files:
        return ""
    
    # Get the code from the first file (they should all have the same code)
    code = files[0].front_matter.get('code', '')
    
    # Create front matter
    front_matter = {
        'code': code,
        'type': 'brain_guide',
        'language': language,
        'status': 'interlinking-ready'
    }
    
    return f"---\n{yaml.dump(front_matter, allow_unicode=True, sort_keys=False)}---\n\n"

def main():
    # Load configuration
    script_dir = Path(__file__).parent
    config_path = script_dir / 'config.json'
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
    except FileNotFoundError:
        print(f"Error: config.json not found at {config_path}")
        return
    except json.JSONDecodeError:
        print("Error: Invalid JSON in config.json")
        return
    
    input_dir = Path(config['input_folder'])
    output_folder_name = config['output_folder']
    translations = config.get('translations', {})
    
    # Get and process markdown files
    markdown_files = get_markdown_files(input_dir)
    if not markdown_files:
        print(f"No markdown files with valid front matter found in {input_dir}")
        return
    
    # Group files by code and language, and by directory
    grouped_files = group_by_code_and_language(markdown_files)
    
    # Process each group
    for group_key, directory_groups in grouped_files.items():
        for directory, files in directory_groups.items():
            # Sort files by order
            sorted_files = sort_markdown_files(files)
            
            # Determine the language for this group
            language = sorted_files[0].front_matter.get('language', 'en')
            
            # Create output directory at the same level as the markdown files directory
            output_dir = directory / output_folder_name
            output_dir.mkdir(exist_ok=True)
            
            # Create output filename
            output_filename = f"{group_key}_temp.md"
            output_path = output_dir / output_filename
            
            # Combine content and write to output file
            with open(output_path, 'w', encoding='utf-8') as f:
                # Write front matter
                f.write(create_output_front_matter(sorted_files, language))
                
                # Write all content sections
                for idx, md_file in enumerate(sorted_files):
                    if idx > 0:  # Add newline between files
                        f.write('\n\n')
                    f.write(f"## {md_file.front_matter.get('title', '')}\n\n{md_file.content}")
                
                # Add references section at the end
                references_text = get_references_text(language, translations)
                f.write(f"\n\n## {references_text}\n")
            
            print(f"Created {output_path}")

if __name__ == "__main__":
    main() 
