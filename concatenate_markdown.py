import os
import yaml

# Define the parent folder where all the drug folders are located
base_folder = "/Users/flavioguzman/Brain Guides/Brain Guides/Antidepressants"

# Function to extract YAML front matter and content from a Markdown file
def parse_markdown(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()
    yaml_lines = []
    content_lines = []
    in_yaml_block = False
    
    # Handle the YAML front matter more carefully
    for line in lines:
        if line.strip() == "---":
            if not in_yaml_block:
                in_yaml_block = True
                continue
            else:
                in_yaml_block = False
                continue
        if in_yaml_block:
            yaml_lines.append(line)
        elif not in_yaml_block and line:  # Only add non-empty lines after YAML block
            content_lines.append(line)
    
    try:
        yaml_data = yaml.safe_load("".join(yaml_lines)) if yaml_lines else {}
        if yaml_data is None:  # Handle empty YAML blocks
            yaml_data = {}
    except yaml.YAMLError as e:
        print(f"Warning: YAML parsing error in {file_path}: {e}")
        yaml_data = {}
    
    return yaml_data, "".join(content_lines)

def process_folder(folder_path):
    # Collect all Markdown files in the folder
    markdown_files = []
    output_filename = None
    for root, _, files in os.walk(folder_path):
        for file in files:
            if file.endswith('.md'):
                # Skip the output file if it exists
                if output_filename and file == output_filename:
                    continue
                markdown_files.append(os.path.join(root, file))
    
    if not markdown_files:
        return
    
    sections = []
    first_yaml = None
    
    for md_path in markdown_files:
        yaml_data, content = parse_markdown(md_path)
        
        # Capture the YAML from the first file
        if not first_yaml:
            first_yaml = yaml_data
        
        # Add section content, including H2 title from YAML `title`
        title_heading = f"## {yaml_data.get('title', '')}\n\n"
        order = yaml_data.get('order')
        if not isinstance(order, (int, float)) or order is None:
            order = 999999
        sections.append((order, title_heading + content))
    
    # Sort and combine sections
    sections.sort(key=lambda x: x[0])
    # Start fresh with just the YAML front matter
    combined_file_content = "---\n" + yaml.dump(first_yaml) + "---\n\n"
    
    # Add each section only once
    for _, section_content in sections:
        combined_file_content += section_content.strip() + "\n\n"
    
    # Add References section (only once)
    combined_file_content += "## References\n"
    
    # Use the `code` field from the first YAML as the output filename
    folder_name = os.path.basename(folder_path)
    output_filename = (first_yaml.get('code') or folder_name or 'output') + ".md"
    output_file = os.path.join(folder_path, output_filename)
    
    # Write the combined content (this will overwrite the existing file)
    with open(output_file, 'w', encoding='utf-8') as output:
        output.write(combined_file_content)

# Main execution
for drug_folder in os.listdir(base_folder):
    drug_path = os.path.join(base_folder, drug_folder)
    if os.path.isdir(drug_path):
        process_folder(drug_path)
        # Process any subdirectories
        for root, dirs, _ in os.walk(drug_path):
            for dir_name in dirs:
                subfolder_path = os.path.join(root, dir_name)
                process_folder(subfolder_path)

print("Consolidation complete!")