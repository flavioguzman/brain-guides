# Link Processing Script Requirements

Create a Python script that processes markdown files to convert wiki-style links to web URLs, with the following requirements:

## Core Functionality
1. Process markdown files to convert wiki-style links (`[[link]]` format) into standard markdown links `[text](url)`
2. Support both single files and directory processing
3. Read YAML from markdown to decide language and file name
4. Handle multiple languages through frontmatter configuration
5. Maintain a status workflow: files marked as `interlinking-ready` → `html-ready` after processing

## Language and Slug Handling
*  Each markdown file has frontmatter containing:

```markdown
---
code: BG007
language: en     # e.g., 'en', 'es', 'it'
order: 1
project advancement: 
status: interlinking-ready
title: Pharmacodynamics and mechanism of action
type:
  - section
---
![imagealttag](https://cdn.psychopharmacologyinstitute.com/%5BGuides%5D/levomilnacipran-pharmacodynamics.png)

* Potent and selective serotonin and norepinephrine reuptake inhibition (SNRI), by blocking SERT and NET.
* Greater potency for norepinephrine reuptake inhibition than serotonin (5HT: NE=1:2)[@Sansone2014].
* Serotonergic effects: 
* ```
* Index files (target files for links) include a frontmatter with language-specific slugs:

```yaml
Venlafaxine.md
---
en-slug: venlafaxine-guide-pharmacology-indications-dosing-guidelines-and-adverse-effects-2888
es-slug:
it-slug: 
code: BG004
id: "2888"
---
```

3. Link Resolution Rules:
   - For a file with `language: en`, use the `en-slug` from the index file
   - For a file with `language: es`, use the `es-slug` from the index file
   - For a file with `language: it`, use the `it-slug` from the index file
Think of a scalable way of mantaining this logic
   - If the corresponding language slug is empty or missing, keep the link as it currently is.

## Configuration
1. Use a JSON config file that specifies:
   - Content source (either local path or GitHub repository)
   - Base URLs for different languages:
     ```json
{

    "base_urls": {

        "en": "https://psychopharmacologyinstitute.com",

        "es": "https://your-site.com/es/guides",

        "it": "https://your-site.com/it/guides"

    },

    "content": {

        "local_path": "/Users/flavioguzman/Documents/Brain Guides/Brain Guides/Antidepressants/Levomilnacipran/Commented copy",

        "index_path": "/Users/flavioguzman/Documents/Brain Guides/Brain Guides/Index",

        "github": {

            "repository": "username/repo-name",

            "branch": "main",

            "content_dir": "content"

        }

    }

}
     ```
   - Index file paths for link resolution
   - GitHub repository details (if using GitHub source)

## Link Processing Rules
1. Support two link formats:
   - Simple: `[[path]]`
   - With alias: `[[path|display text]]`
2. When processing a link:
   - Read the source file's language from its frontmatter
   - Find the corresponding index file
   - Extract the appropriate language-specific slug
   - Combine with the language-specific base URL
   - Generate final URL format: `[display_text](base_url/language-specific-slug)`

## File Handling
1. Generate output files with language-specific naming:
   - English: `{code from the code property, in the example above would be BG007}.md`
   - Other languages: `BG007_[lang].md` (e.g., `filename_es.md`)
2. Preserve original files
3. Support index file caching for better performance

## Input Validation
1. Only process files with frontmatter status `interlinking-ready`
2. Validate:
   - Presence of `language` in source file frontmatter
   - Existence of corresponding language slug in index files
   - Valid base URLs for each language
3. Handle missing index files gracefully with warnings

## Command Line Interface
Support the following arguments:
- `--verbose`: Enable detailed warnings

## Error Handling
1. Proper error handling for:
   - Missing language specifications
   - Missing or empty language-specific slugs
   - Invalid paths
   - File access issues
   - YAML parsing errors
2. Cleanup of temporary files (when using GitHub)

## Output
1. Update frontmatter status to `html-ready` after processing
2. Generate new files with processed content
3. Provide progress and error logging, including:
   - Missing language slugs
   - Unresolved links
   - Language mismatches

