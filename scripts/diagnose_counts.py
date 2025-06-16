import sys
from pathlib import Path

# Ensure shared_tools is discoverable when running from project root
sys.path.append('CorpusBuilderApp')

from shared_tools.project_config import ProjectConfig
from shared_tools.ui_wrappers.wrapper_factory import create_processor_wrapper  # noqa: F401 (side-effect import ensures wrappers register)


CFG_PATH = 'CorpusBuilderApp/configs/local_corpus.yaml'
CFG_ENV = 'local'


def main():
    cfg = ProjectConfig(CFG_PATH, environment=CFG_ENV)
    raw_dir = Path(cfg.get_raw_dir())
    if not raw_dir.exists():
        print(f"Raw directory does not exist: {raw_dir}")
        return

    wrappers = ('pdf', 'text', 'pdf_batch', 'text_batch')
    for key in wrappers:
        patterns = ('*.pdf', '*.PDF') if 'pdf' in key else ('*.txt', '*.md', '*.html', '*.htm')
        files = [p for pat in patterns for p in raw_dir.rglob(pat)]
        print(f"{key:<10} scans {raw_dir}, found {len(files)} matching files")


if __name__ == '__main__':
    main() 