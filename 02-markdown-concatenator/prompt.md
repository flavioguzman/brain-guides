I need a Python script that combines multiple Markdown files in a directory into one. The script should:
	1.	Combine all Markdown files in the same directory.
	2.	Determine the order in which the files are combined using the order key in the YAML front matter of each file.
	3.	Dynamically name the output file based on the code and language keys in the YAML:
	•	If the language is en, the output file should be named {code}_temp.md.
	•	If the language is not en, the output file should be named {code}_{language}_temp.md.
	4.	Save the output file in a separate folder at the same level as the found markdown files. If the output folder does not exist, the script should create it.

The script should respect the content of the files and not modify it. It should not include the YAML front matter in the output file.   

The intput folder path and the output folder name   would be defined in a config.json file. The script should process the files in the folder defined in the config.json file and its subfolders.   

Here is an example of the YAML front matter from one of the Markdown files:

---
code: BG007
title: Pharmacodynamics and mechanism of action
order: 1
project advancement: []
language: en
type: section
---

