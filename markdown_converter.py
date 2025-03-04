import subprocess
import json
import os
from pathlib import Path

class MarkdownConverter:
    def __init__(self, config_path="config.json"):
        print(f"Loading config from: {os.path.abspath(config_path)}")
        self.config = self._load_config(config_path)
        print(f"Loaded config: {self.config}")
        self.bib_path = self.config.get("bibliography_path")
        self.csl_path = self.config.get("csl_path")
        self.input_path = self.config.get("input_path")
        
        # Create Lua filter files if they don't exist
        self._ensure_lua_filters()
        
        if not self.bib_path or not os.path.exists(self.bib_path):
            raise FileNotFoundError(f"Bibliography file not found at {self.bib_path}")
        
        if self.csl_path and not os.path.exists(self.csl_path):
            raise FileNotFoundError(f"CSL file not found at {self.csl_path}")
            
        if not self.input_path or not os.path.exists(self.input_path):
            raise FileNotFoundError(f"Input markdown file not found at {self.input_path}")

    def _load_config(self, config_path):
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
                print(f"Successfully loaded config from {config_path}")
                return config
        except FileNotFoundError:
            print(f"Config file not found at {config_path}, creating default config")
            # Create default config if it doesn't exist
            default_config = {
                "bibliography_path": "/Users/sebastianmalleza/Desktop/Brain Guides.bib",
                "csl_path": "ieee.csl",
                "default_output_format": "html",
                "input_path": "example.md"
            }
            with open(config_path, 'w') as f:
                json.dump(default_config, f, indent=4)
            return default_config

    def _ensure_lua_filters(self):
        """Create Lua filter files if they don't exist."""
        if not os.path.exists("image-size.lua"):
            with open("image-size.lua", "w") as lua_file:
                lua_file.write("""
                function Image (img)
                    img.attributes['style'] = 'width: 50%;'
                    return img
                end
                """)

        if not os.path.exists("reference-list.lua"):
            with open("reference-list.lua", "w") as lua_file:
                lua_file.write("""
                function Div (div)
                    if div.classes[1] == "references" then
                        local list = pandoc.List({})
                        for _, item in ipairs(div.content) do
                            if item.t == "Div" and item.classes[1] == "csl-entry" then
                                list:insert(pandoc.BulletList({pandoc.Para(item.content)}))
                            end
                        end
                        return pandoc.Div(list, {class = "references"})
                    end
                    return div
                end
                """)

        # Add new filter for removing captions
        if not os.path.exists("remove-captions.lua"):
            with open("remove-captions.lua", "w") as lua_file:
                lua_file.write("""
                function Image (img)
                    img.caption = pandoc.List({})  -- Remove caption
                    img.title = ""  -- Remove title
                    return img
                end
                """)

    def convert(self, output_path=None, output_format=None):
        """
        Convert markdown file with citations to HTML or markdown
        
        Args:
            output_path (str, optional): Path for output file. If None, will use input filename with new extension
            output_format (str, optional): Either "html" or "markdown". If None, uses config default
        """
        if not output_format:
            output_format = self.config.get("default_output_format", "html")
            
        # Convert 'md' to 'markdown' for pandoc compatibility
        pandoc_format = "markdown" if output_format == "md" else output_format
        
        if not output_path:
            input_file = Path(self.input_path)
            output_path = str(input_file.with_suffix(f".{output_format}"))

        # Add debug logging
        print(f"Using bibliography file: {self.bib_path}")
        try:
            with open(self.bib_path, 'r', encoding='utf-8') as f:
                bib_content = f.read()
                print(f"Bibliography file loaded successfully ({len(bib_content)} bytes)")
        except Exception as e:
            print(f"Error reading bibliography file: {e}")
            return

        cmd = [
            "pandoc",
            self.input_path,
            "-f", "markdown",
            "-t", pandoc_format,
            "--bibliography", self.bib_path,
            "--citeproc",
            "--lua-filter", "citation-spacing.lua",
            "--lua-filter", "image-size.lua",
            "--lua-filter", "reference-list.lua",
            "--lua-filter", "remove-captions.lua",
            "-o", output_path,
            "--verbose"
        ]

        if self.csl_path:
            cmd.extend(["--csl", self.csl_path])

        try:
            subprocess.run(cmd, check=True)
            print(f"Successfully converted {self.input_path} to {output_path}")
        except subprocess.CalledProcessError as e:
            print(f"Error converting file: {e}")
        except FileNotFoundError:
            print("Error: Pandoc is not installed. Please install pandoc first.")

if __name__ == "__main__":
    # Example usage
    converter = MarkdownConverter()
    converter.convert() 