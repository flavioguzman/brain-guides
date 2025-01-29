#!/usr/bin/env python3

import os
import re
import json
import yaml
import argparse
from pathlib import Path
from typing import Dict, Optional, Tuple

class LinkProcessor:
    def __init__(self, config_path: str, verbose: bool = False):
        self.verbose = verbose
        self.config = self._load_config(config_path)
        self.index_cache = {}
        
        # Validate required config values
        self._validate_config()
        
        # Run path resolution tests if verbose
        if verbose:
            self._test_path_resolution()
        
    def _load_config(self, config_path: str) -> dict:
        """Load configuration from JSON file."""
        try:
            if not os.path.exists(config_path):
                raise FileNotFoundError(f"Config file not found: {config_path}")
                
            with open(config_path, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            raise Exception(f"Invalid JSON in config file: {str(e)}")
        except Exception as e:
            raise Exception(f"Failed to load config file: {str(e)}")
            
    def _validate_config(self):
        """Validate that all required configuration values are present."""
        required_keys = {
            'base_urls': ['en'],  # At least English base URL is required
            'content': ['local_path', 'index_path']
        }
        
        missing = []
        
        # Check top-level keys
        for key in required_keys:
            if key not in self.config:
                missing.append(key)
                continue
                
            # Check nested keys
            for nested_key in required_keys[key]:
                if nested_key not in self.config[key]:
                    missing.append(f"{key}.{nested_key}")
                    
        if missing:
            raise ValueError(f"Missing required configuration values: {', '.join(missing)}")
            
        # Validate paths exist
        local_path = self.config['content']['local_path']
        index_path = self.config['content']['index_path']
        
        if not os.path.exists(local_path):
            raise ValueError(f"Content path does not exist: {local_path}")
        if not os.path.exists(index_path):
            raise ValueError(f"Index path does not exist: {index_path}")

    def _parse_frontmatter(self, content: str) -> Tuple[dict, str]:
        """Extract YAML frontmatter and content from markdown file."""
        if not content.startswith('---'):
            return {}, content
            
        parts = content.split('---', 2)
        if len(parts) < 3:
            return {}, content
            
        try:
            frontmatter = yaml.safe_load(parts[1])
            return frontmatter, parts[2]
        except yaml.YAMLError as e:
            raise Exception(f"Failed to parse frontmatter: {str(e)}")

    def _load_index_file(self, index_path: str) -> dict:
        """Load and cache index file content."""
        if index_path in self.index_cache:
            return self.index_cache[index_path]
            
        try:
            with open(index_path, 'r') as f:
                content = f.read()
            frontmatter, _ = self._parse_frontmatter(content)
            self.index_cache[index_path] = frontmatter
            return frontmatter
        except Exception as e:
            if self.verbose:
                print(f"Warning: Failed to load index file {index_path}: {str(e)}")
            return {}

    def _get_language_slug(self, index_data: dict, language: str) -> Optional[str]:
        """Get language-specific slug from index data."""
        slug_key = f"{language}-slug"
        return index_data.get(slug_key)

    def _resolve_path(self, relative_path: str) -> str:
        """Convert relative path to absolute path relative to index directory."""
        # Convert path to use forward slashes and remove any file extension
        clean_path = relative_path.replace('\\', '/')
        clean_path = os.path.splitext(clean_path)[0]
        
        # Split the path into components
        parts = [p for p in clean_path.split('/') if p and p not in ('..', '.', 'Index', 'Brain Guides')]
        
        # For paths like 'Drugs/Venlafaxine', we want to keep them as is
        return '/'.join(parts)

    def _process_link(self, match: re.Match, language: str) -> str:
        """Process a single wiki-style link."""
        link_content = match.group(1)
        display_text = link_content
        
        # Handle aliased links
        if '|' in link_content:
            path, display_text = link_content.split('|', 1)
        else:
            path = link_content
            # Use the last part of the path as display text if no alias
            display_text = os.path.basename(path)

        # Clean up the path
        clean_path = self._resolve_path(path)
        
        # Find corresponding index file
        index_path = os.path.normpath(os.path.join(self.config['content']['index_path'], f"{clean_path}.md"))
        
        if self.verbose:
            print(f"Processing link:")
            print(f"  Original: {link_content}")
            print(f"  Display text: {display_text}")
            print(f"  Clean path: {clean_path}")
            print(f"  Looking for index file at: {index_path}")
            
        index_data = self._load_index_file(index_path)
        if not index_data and self.verbose:
            print(f"  Warning: No index data found")
            
        # Get language-specific slug
        slug = self._get_language_slug(index_data, language)
        if not slug:
            if self.verbose:
                print(f"  Warning: No {language} slug found")
            return f"[[{link_content}]]"  # Keep original link if no slug found
            
        # Construct final URL
        base_url = self.config['base_urls'].get(language)
        if not base_url:
            if self.verbose:
                print(f"  Warning: No base URL configured for language {language}")
            return f"[[{link_content}]]"
            
        final_url = f"{base_url}/{slug}"
        if self.verbose:
            print(f"  Generated URL: {final_url}")
            
        return f"[{display_text}]({final_url})"

    def process_file(self, file_path: str) -> Optional[str]:
        """Process a single markdown file."""
        try:
            with open(file_path, 'r') as f:
                content = f.read()
                
            # Parse frontmatter
            frontmatter, markdown_content = self._parse_frontmatter(content)
            
            # Validate file is ready for processing
            if frontmatter.get('status') != 'interlinking-ready':
                if self.verbose:
                    print(f"Skipping {file_path}: Not ready for interlinking")
                return None
                
            language = frontmatter.get('language')
            if not language:
                if self.verbose:
                    print(f"Skipping {file_path}: No language specified")
                return None
                
            # Process links
            def replace_link(match):
                return self._process_link(match, language)
                
            processed_content = re.sub(r'\[\[(.*?)\]\]', replace_link, markdown_content)
            
            # Update frontmatter
            frontmatter['status'] = 'html-ready'
            
            # Construct output
            output_content = "---\n"
            output_content += yaml.dump(frontmatter, allow_unicode=True)
            output_content += "---\n"
            output_content += processed_content
            
            return output_content
            
        except Exception as e:
            if self.verbose:
                print(f"Error processing file {file_path}: {str(e)}")
            return None

    def save_processed_file(self, original_path: str, content: str) -> None:
        """Save processed content to a new file."""
        try:
            path = Path(original_path)
            frontmatter, _ = self._parse_frontmatter(content)
            
            # Determine output filename
            code = frontmatter.get('code', path.stem)
            language = frontmatter.get('language', 'en')
            
            if language == 'en':
                output_filename = f"{code}.md"
            else:
                output_filename = f"{code}_{language}.md"
                
            output_path = path.parent / output_filename
            
            with open(output_path, 'w') as f:
                f.write(content)
                
            if self.verbose:
                print(f"Saved processed file to {output_path}")
                
        except Exception as e:
            if self.verbose:
                print(f"Error saving processed file: {str(e)}")

    def _test_path_resolution(self):
        """Test path resolution with various input formats."""
        test_cases = [
            ("../../../Index/Drugs/Venlafaxine", "Drugs/Venlafaxine"),
            ("../../../Brain Guides/Index/Drugs/Venlafaxine", "Drugs/Venlafaxine"),
            ("Index/Drugs/Venlafaxine", "Drugs/Venlafaxine"),
            ("Brain Guides/Index/Drugs/Venlafaxine", "Drugs/Venlafaxine"),
            ("Drugs/Venlafaxine", "Drugs/Venlafaxine"),
            ("../../../Index/Drugs/Venlafaxine.md", "Drugs/Venlafaxine"),
        ]
        
        if self.verbose:
            print("\nTesting path resolution:")
            for input_path, expected in test_cases:
                result = self._resolve_path(input_path)
                print(f"  Input:    {input_path}")
                print(f"  Expected: {expected}")
                print(f"  Got:      {result}")
                print(f"  {'✓' if result == expected else '✗'}")
                print()

def main():
    parser = argparse.ArgumentParser(description='Process markdown files to convert wiki-style links to web URLs.')
    parser.add_argument('--config', help='Path to configuration JSON file (default: config.json in script directory)')
    parser.add_argument('--input', help='Input file or directory path (default: uses local_path from config.json)')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose output')
    
    args = parser.parse_args()
    
    try:
        # If no config path is provided, use config.json from the script's directory
        if not args.config:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            config_path = os.path.join(script_dir, 'config.json')
        else:
            config_path = args.config
            
        processor = LinkProcessor(config_path, args.verbose)
        
        # If no input is specified, use the local_path from config
        input_path = args.input or processor.config['content']['local_path']
        
        if os.path.isfile(input_path):
            # Process single file
            content = processor.process_file(input_path)
            if content:
                processor.save_processed_file(input_path, content)
        elif os.path.isdir(input_path):
            # Process directory
            for root, _, files in os.walk(input_path):
                for file in files:
                    if file.endswith('.md'):
                        file_path = os.path.join(root, file)
                        content = processor.process_file(file_path)
                        if content:
                            processor.save_processed_file(file_path, content)
        else:
            print(f"Error: Input path {input_path} does not exist")
            
    except Exception as e:
        print(f"Error: {str(e)}")
        if args.verbose:
            import traceback
            print("\nFull traceback:")
            print(traceback.format_exc())
        exit(1)

if __name__ == "__main__":
    main()