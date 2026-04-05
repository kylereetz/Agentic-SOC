import os

MAPPING = {
    "ANSER": "SYRINX"
}

def get_replacements():
    replacements = []
    
    for old, new in MAPPING.items():
        replacements.append((old, new))
        replacements.append((old.lower(), new.lower()))
        replacements.append((old.title(), new.title()))
        
    replacements.sort(key=lambda x: len(x[0]), reverse=True)
    return replacements

def modify_files(ROOT):
    EXCLUDE_DIRS = {'.git', 'node_modules', 'dist', 'build', '.venv', '.pytest_cache', '__pycache__', '.agents', '.gemini', 'cemetery', 'processed', 'investigation_reasoning', 'case_updates'}
    replacements = get_replacements()
    
    # 1. Content Replacements
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIRS]
        for filename in filenames:
            if filename in ["refactor.py", "refactor_strategist.py", "fix_remaining.py", "swap_syrinx.py"]:
                continue
            filepath = os.path.join(dirpath, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                new_content = content
                for old_val, new_val in replacements:
                    new_content = new_content.replace(old_val, new_val)
                
                if new_content != content:
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                    print(f"Updated content in: {filepath}")
            except UnicodeDecodeError:
                pass
            except Exception as e:
                pass

    # 2. File renames 
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIRS]
        for filename in filenames:
            new_filename = filename
            for old_val, new_val in replacements:
                if old_val in new_filename:
                    new_filename = new_filename.replace(old_val, new_val)
            
            if new_filename != filename:
                old_filepath = os.path.join(dirpath, filename)
                new_filepath = os.path.join(dirpath, new_filename)
                try:
                    os.rename(old_filepath, new_filepath)
                    print(f"Renamed: {old_filepath} -> {new_filepath}")
                except Exception as e:
                    print(f"Error renaming {old_filepath}: {e}")

if __name__ == "__main__":
    ROOT_DIR = r"c:\Users\kyler\Documents\GitHub\Agentic SOC"
    modify_files(ROOT_DIR)
    print("Syrinx swap complete.")
