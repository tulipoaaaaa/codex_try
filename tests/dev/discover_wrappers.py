import os
import importlib
import inspect
from pathlib import Path
from PySide6.QtCore import QObject

def discover_wrapper_classes():
    """Discover all wrapper classes in the processors directory."""
    wrapper_paths = []
    processors_dir = Path("CorpusBuilderApp/shared_tools/ui_wrappers/processors")
    
    # Walk through all .py files in the directory
    for py_file in processors_dir.glob("*.py"):
        if py_file.name == "__init__.py":
            continue
            
        # Convert file path to module path
        module_path = str(py_file.relative_to("CorpusBuilderApp")).replace(os.sep, ".")[:-3]
        module_path = f"CorpusBuilderApp.{module_path}"
        
        try:
            # Import the module
            module = importlib.import_module(module_path)
            
            # Find all classes in the module
            for name, obj in inspect.getmembers(module):
                # Check if it's a class, ends with Wrapper, and is a QObject subclass
                if (inspect.isclass(obj) and 
                    name.endswith("Wrapper") and 
                    issubclass(obj, QObject) and 
                    obj != QObject):  # Exclude QObject itself
                    wrapper_paths.append(f"{module_path}.{name}")
                    
        except Exception as e:
            print(f"Error importing {module_path}: {e}")
            continue
    
    return sorted(wrapper_paths)

if __name__ == "__main__":
    wrapper_paths = discover_wrapper_classes()
    
    # Assert that we found at least one wrapper
    assert wrapper_paths, "No wrapper classes found!"
    
    # Print each wrapper path
    for path in wrapper_paths:
        print(path) 