import os

def generate_tree_and_contents(root_path, output_file):
    tree_lines = []
    content_lines = []

    # Generate folder & file tree
    for root, dirs, files in os.walk(root_path):
        level = root.replace(root_path, '').count(os.sep)
        indent = '│   ' * (level - 1) + ('├── ' if level > 0 else '')
        tree_lines.append(f"{indent}{os.path.basename(root)}/")

        for f in files:
            file_indent = '│   ' * level + '├── '
            tree_lines.append(f"{file_indent}{f}")

            full_path = os.path.join(root, f)

            # Read file content safely
            try:
                with open(full_path, "r", encoding="utf-8", errors="ignore") as file:
                    content = file.read()
            except Exception as e:
                content = f"[Could not read file: {e}]"

            content_lines.append("\n" + "="*80)
            content_lines.append(f"FILE: {full_path}")
            content_lines.append("="*80 + "\n")
            content_lines.append(content)

    # Combine everything & save to output file
    with open(output_file, "w", encoding="utf-8") as out:
        out.write("### DIRECTORY TREE ###\n\n")
        out.write("\n".join(tree_lines))
        out.write("\n\n### FILE CONTENTS ###\n\n")
        out.write("\n".join(content_lines))

    print(f"Output saved to: {output_file}")


if __name__ == "__main__":
    root = input("Enter the folder path: ").strip()
    output = "folder_dump.txt"
    generate_tree_and_contents(root, output)
