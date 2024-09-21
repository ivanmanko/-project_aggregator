import os
import sys
from pathlib import Path
import argparse
import pathspec

def load_gitignore_patterns(gitignore_path):
    """
    Load patterns from a .gitignore file using pathspec.
    """
    try:
        with open(gitignore_path, 'r') as f:
            patterns = f.read().splitlines()
        spec = pathspec.PathSpec.from_lines(pathspec.patterns.GitWildMatchPattern, patterns)
        return spec
    except FileNotFoundError:
        print(f"No .gitignore file found at {gitignore_path}. Proceeding without exclusion.")
        return pathspec.PathSpec.from_lines(pathspec.patterns.GitWildMatchPattern, [])

def should_exclude(path, spec, special_exclude):
    """
    Determine if a path should be excluded based on .gitignore patterns or special exclusions.
    """
    # Convert to POSIX style for pathspec compatibility
    posix_path = path.as_posix()
    if spec.match_file(posix_path):
        return True
    if posix_path == special_exclude:
        return True
    return False

def aggregate_project_contents(root_dir, output_file, special_exclude='.aggregate_exclude'):
    """
    Traverse the directory, exclude specified files, and aggregate contents into a single file.
    """
    root = Path(root_dir).resolve()
    gitignore_path = root / '.gitignore'
    spec = load_gitignore_patterns(gitignore_path)

    with open(output_file, 'w', encoding='utf-8') as outfile:
        for dirpath, dirnames, filenames in os.walk(root):
            current_dir = Path(dirpath)
            # Compute relative path from root
            rel_dir = current_dir.relative_to(root)

            # Modify dirnames in-place to exclude ignored directories
            dirnames[:] = [
                d for d in dirnames 
                if not should_exclude(current_dir / d, spec, special_exclude)
            ]

            for filename in filenames:
                file_path = current_dir / filename
                rel_file_path = file_path.relative_to(root)

                if should_exclude(rel_file_path, spec, special_exclude):
                    continue

                # Write the relative file path
                outfile.write(f"--- {rel_file_path.as_posix()} ---\n")

                try:
                    with open(file_path, 'r', encoding='utf-8') as infile:
                        content = infile.read()
                    outfile.write(content)
                except (UnicodeDecodeError, PermissionError) as e:
                    outfile.write(f"[Could not read file: {e}]\n")
                except Exception as e:
                    outfile.write(f"[Unexpected error: {e}]\n")

                outfile.write("\n\n")  # Separator between files

    print(f"All contents have been aggregated into {output_file}")

def main():
    parser = argparse.ArgumentParser(description="Aggregate project files into a single text file.")
    parser.add_argument(
        '-o', '--output', 
        type=str, 
        default='project_contents.txt', 
        help='Name of the output text file.'
    )
    parser.add_argument(
        '-s', '--special', 
        type=str, 
        default='.aggregate_exclude', 
        help='Special file to exclude from aggregation.'
    )
    args = parser.parse_args()

    current_dir = Path.cwd()
    aggregate_project_contents(current_dir, args.output, args.special)

if __name__ == "__main__":
    main()
