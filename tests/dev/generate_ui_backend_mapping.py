import os
import ast
import re
from collections import defaultdict

# Directories to scan (updated for actual project structure)
SCAN_DIRS = [
    os.path.join('CorpusBuilderApp', 'app'),
    os.path.join('CorpusBuilderApp', 'shared_tools'),
]

# Output files
MAPPING_FILE = os.path.abspath(os.path.join('G:/codex/codex_try/Mapping_UI_backend.txt'))
CHECKED_FILE = os.path.abspath(os.path.join('G:/codex/codex_try/Mapping_UI_backend_checked.txt'))

# Helper: find all python files in scan dirs
def all_python_files():
    py_files = []
    for scan_dir in SCAN_DIRS:
        for root, dirs, files in os.walk(scan_dir):
            for fname in files:
                if fname.endswith('.py') and fname != '__init__.py':
                    py_files.append(os.path.join(root, fname))
    return py_files

# Helper: build a map of class name -> (filepath, ast.ClassDef)
def build_class_map():
    class_map = defaultdict(list)
    for fpath in all_python_files():
        try:
            with open(fpath, 'r', encoding='utf-8') as f:
                src = f.read()
            tree = ast.parse(src, filename=fpath)
        except Exception:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                class_map[node.name].append((fpath, node))
    return class_map

# Helper: check if class has attribute/method
def class_has_attr(class_node, name):
    for node in class_node.body:
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return True
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name) and t.id == name:
                    return True
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) and node.target.id == name:
            return True
        if isinstance(node, ast.ClassDef) and node.name == name:
            return True
    return False

def main():
    class_map = build_class_map()
    checked_lines = []
    missing = []
    total_checked = 0
    with open(MAPPING_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or '-->' not in line:
                continue
            ui_class, backend_ref = [x.strip() for x in line.split('-->')]
            # Only check <BackendClass>.<name> where BackendClass is not 'self' or 'lambda'
            m = re.match(r'([A-Za-z_][A-Za-z0-9_]*)\.([A-Za-z_][A-Za-z0-9_]*)$', backend_ref)
            if m:
                backend_class, attr = m.group(1), m.group(2)
                found = False
                if backend_class in class_map:
                    for fpath, class_node in class_map[backend_class]:
                        if class_has_attr(class_node, attr):
                            found = True
                            break
                if found:
                    checked_lines.append(line)
                else:
                    missing.append(f"[MISSING] {ui_class} expects {backend_class}.{attr}")
                    checked_lines.append(f"[MISSING] {ui_class} expects {backend_class}.{attr}")
                total_checked += 1
            else:
                # Don't check self., lambda, or other non-backend refs
                checked_lines.append(line)
    with open(CHECKED_FILE, 'w', encoding='utf-8') as out:
        for l in checked_lines:
            out.write(l + '\n')
    print(f"Checked backend references: {total_checked}")
    print(f"Missing/invalid references: {len(missing)}")
    if missing:
        print("Missing entries:")
        for m in missing:
            print(m)
    else:
        print("No missing backend attributes/methods found.")

if __name__ == '__main__':
    main() 