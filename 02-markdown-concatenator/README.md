# Markdown Concatenator

A Python script that combines multiple Markdown files into a single document, respecting YAML front matter for ordering and language-specific output.

## Features

- Combines multiple Markdown files based on their YAML front matter
- Only processes files marked as type 'section'
- Maintains file order using the `order` key in front matter
- Supports multiple languages with language-specific output files
- Automatically adds a language-specific references section
- Creates output in a separate folder at the same level as input files
- Preserves content formatting while removing original front matter
- Converts titles from front matter into H2 headings
- Adds new YAML front matter to output files with type 'brain_guide' and status 'interlinking-ready'

## Installation

1. Make sure you have Python 3.6 or newer installed on your system
   - For Windows: Download and install from [python.org](https://www.python.org/downloads/)
   - For Mac: Python comes pre-installed
   - For Linux: Use your package manager or download from python.org

2. Install the required PyYAML package:
   - Open Terminal (Mac/Linux) or Command Prompt (Windows)
   - Run: `pip install pyyaml`

## Configuration

The script uses a `config.json` file for configuration:

```json
{
    "input_folder": "/path/to/input/directory",
    "output_folder": "Website",
    "translations": {
        "references": {
            "en": "References",
            "es": "Referencias",
            "fr": "Références",
            "pt": "Referências",
            "it": "Riferimenti",
            "de": "Literatur"
        }
    }
}
```

### Configuration Options

- `input_folder`: Full path to the directory containing your markdown files
- `output_folder`: Name of the output folder to create (e.g., "Website")
- `translations`: Dictionary of translations for the "References" section heading

## Input File Requirements

Each markdown file must have YAML front matter with these fields:

```yaml
---
code: BG007           # Required: Used for grouping files
title: Section Title  # Required: Will be converted to H2 heading
order: 1              # Required: Determines file order in output
type: section         # Required: Must be 'section' or include 'section' in list
language: en          # Optional: Defaults to 'en'
---
```

Important notes about the front matter:
- The `type` field must be either:
  ```yaml
  type: section
  ```
  or
  ```yaml
  type:
    - section
  ```
- Files without `type: section` will be ignored
- The order of the keys doesn't matter
- All fields except `language` are required

## Output Structure

The script creates output files following these rules:

1. For English content (language: en):
   - Filename: `{code}_temp.md`
2. For other languages:
   - Filename: `{code}_{language}_temp.md`

Output files are created in a new folder (specified by `output_folder` in config) at the same level as your markdown files.

### Output Format

The combined file will contain:
1. New YAML front matter with:
   ```yaml
   ---
   code: BG007                    # Inherited from input files
   type: brain_guide              # Always set to 'brain_guide'
   language: en                   # Based on input files
   status: interlinking-ready     # Always set to 'interlinking-ready'
   ---
   ```
2. Each section's title as an H2 heading
3. The content from each file
4. A language-specific "References" section at the end

## Usage for Non-Developers

1. First-time setup:
   - Install Python from [python.org](https://www.python.org/downloads/)
   - Open Terminal (Mac) or Command Prompt (Windows)
   - Install PyYAML by typing: `pip install pyyaml`

2. Configure the script:
   - Open `config.json` in a text editor
   - Update the `input_folder` path to point to your markdown files
   - Set `output_folder` to your desired output folder name (e.g., "Website")

3. Run the script:
   - Open Terminal (Mac) or Command Prompt (Windows)
   - Navigate to the script's directory:
     ```bash
     cd path/to/script/directory
     ```
   - Run the script:
     ```bash
     python concatenate_markdown.py
     ```

4. Find your output:
   - Look for a new folder (named as per your `output_folder` setting)
   - It will be created at the same level as your markdown files
   - Inside will be the combined markdown files

## Example

Starting structure:
```
Documents/
└── Brain Guides/
    └── Antidepressants/
        └── Drug Name/
            └── Sections/
                ├── 01-intro.md
                └── 02-mechanism.md
```

After running the script:
```
Documents/
└── Brain Guides/
    └── Antidepressants/
        └── Drug Name/
            ├── Website/                  # New folder
            │   └── BG007_temp.md        # Combined file
            └── Sections/
                ├── 01-intro.md
                └── 02-mechanism.md
```

## Troubleshooting

Common issues and solutions:

1. "No markdown files found":
   - Check that your input files have the correct YAML front matter
   - Verify that they include `type: section`
   - Make sure the input path in config.json is correct

2. "Module not found" error:
   - Run `pip install pyyaml` again
   - Make sure Python is properly installed

3. Files not combining correctly:
   - Check that all files have the required YAML fields
   - Verify the `order` numbers are correct
   - Make sure all files have the same `code` value

4. Output in wrong location:
   - Check your `output_folder` setting in config.json
   - Verify file permissions in the target directory

## Notes

- Files without valid front matter are ignored
- Files without `type: section` are ignored
- The script creates fresh output files each time (overwriting existing ones)
- Empty directories are skipped
- YAML front matter key order is irrelevant
- All output files are marked with `status: interlinking-ready` 