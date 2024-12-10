# Brain Guides Document Processing System

This repository contains a collection of scripts for processing and formatting markdown documents, specifically designed for Brain Guides documentation. The system handles document concatenation, citation formatting, and image processing.

## Core Components

### Python Scripts

- `markdown_converter.py`: The main conversion script that processes markdown files into various output formats (primarily HTML). It integrates with Pandoc and applies various Lua filters during the conversion process.

- `concatenate_markdown.py`: Combines multiple markdown files within drug-specific folders into single consolidated documents. It:
  - Preserves YAML front matter from the first file
  - Orders sections based on the `order` field in YAML
  - Automatically adds a References section
  - Names output files based on the `code` field from YAML

### Lua Filters

- `remove-captions.lua`: Removes captions, titles, and alt text from images and figures when `remove_captions` is set to true in the configuration.

- `image-size.lua`: Sets a consistent width (80%) for all images in the document for better visual presentation.

- `reference-list.lua`: Formats the references section with custom styling for better readability and mobile responsiveness.

- `citation-spacing.lua`: Ensures proper spacing around citations in the text.

## Configuration

The system is configured through `config.json`, which specifies:
- Bibliography file path
- Citation Style Language (CSL) file path
- Default output format
- Input file path
- Caption removal preferences

## Workflow

1. Source markdown files are organized in drug-specific folders
2. `concatenate_markdown.py` combines related files into a single document
3. `markdown_converter.py` processes the consolidated file through Pandoc
4. Lua filters are applied during conversion to handle:
   - Image formatting
   - Citation styling
   - Reference list formatting
   - Caption management

## Dependencies

- Python 3.x
- Pandoc
- PyYAML (for markdown concatenation) 