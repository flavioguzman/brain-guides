# Markdown Link Processor

This script processes markdown files to convert wiki-style links (`[[link]]`) into standard markdown links with web URLs, supporting multiple languages through frontmatter configuration.

## Requirements

- Python 3.7+
- Required packages:
  ```
  pyyaml>=6.0.1
  ```

## Installation

1. Clone this repository or download the files
2. Install required packages:
   ```bash
   pip install -r requirements.txt
   ```
3. Configure your `config.json` file with appropriate settings

## Configuration

Create a `config.json` file in the same directory as the script:

```json
{
    "base_urls": {
        "en": "https://psychopharmacologyinstitute.com",
        "es": "https://your-site.com/es/guides",
        "it": "https://your-site.com/it/guides"
    },
    "content": {
        "local_path": "/path/to/markdown/files",
        "index_path": "/path/to/index/files",
        "github": {
            "repository": "username/repo-name",
            "branch": "main",
            "content_dir": "content"
        }
    }
}
```

### Configuration Options

- `base_urls`: URLs for different language versions of your site
  - Must include at least `en` for English
  - Other languages are optional (e.g., `es`, `it`)
- `content`:
  - `local_path`: Directory containing markdown files to process
  - `index_path`: Directory containing index files with slugs
  - `github`: (Optional) GitHub repository settings

## Usage

The script can be run in several ways:

1. Process files using settings from config.json:
```bash
python process_links.py
```

2. Enable verbose output for debugging:
```bash
python process_links.py --verbose
```

3. Use a custom config file:
```bash
python process_links.py --config /path/to/config.json
```

4. Process a specific file or directory:
```bash
python process_links.py --input /path/to/file.md
```

## File Requirements

### Source Files
Each markdown file should have frontmatter containing:
```yaml
---
code: BG007
language: en     # 'en', 'es', or 'it'
status: interlinking-ready
---
```

### Index Files
Index files should have language-specific slugs in frontmatter:
```yaml
---
en-slug: english-page-slug
es-slug: spanish-page-slug
it-slug: italian-page-slug
code: BG004
id: "2888"
---
```

## Link Processing

The script supports two link formats:
1. Simple: `[[path/to/file]]`
2. With alias: `[[path/to/file|display text]]`

### Path Resolution
The script handles various path formats:
- Relative paths: `../../../Index/Drugs/Venlafaxine`
- Direct paths: `Index/Drugs/Venlafaxine`
- Clean paths: `Drugs/Venlafaxine`

All paths are normalized to remove:
- Leading `../` sequences
- `Index/` and `Brain Guides/` prefixes
- File extensions

## Output

- Files are saved with language-specific naming:
  - English: `{code}.md`
  - Other languages: `{code}_{lang}.md`
- Original files are preserved
- Frontmatter status is updated to `html-ready`
- Links are converted to: `[display text](base_url/slug)`

## Error Handling

The script includes comprehensive error handling for:
- Missing or invalid configuration
- Non-existent paths
- Missing language specifications
- Missing or empty language-specific slugs
- File access issues
- YAML parsing errors

Use the `--verbose` flag to see detailed warnings and error messages. 