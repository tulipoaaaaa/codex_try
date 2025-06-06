# sources/repo_collector.py
from CryptoFinanceCorpusBuilder.shared_tools.collectors.base_collector import BaseCollector
import subprocess
import os
import shutil
import tempfile
from pathlib import Path

class RepoCollector(BaseCollector):
    """Base class for collecting from code repositories (e.g., GitHub)"""
    
    def __init__(self, config, delay_range=(2, 5), clone_depth=1):
        if isinstance(config, str):
            from shared_tools.project_config import ProjectConfig
            config = ProjectConfig(config, environment='test')
        super().__init__(config, delay_range)
        self.clone_depth = clone_depth
    
    def clone_repo(self, repo_url, target_dir=None, branch=None):
        """Clone a git repository"""
        if target_dir is None:
            # Extract repo name from URL
            repo_name = repo_url.split('/')[-1]
            if repo_name.endswith('.git'):
                repo_name = repo_name[:-4]
            target_dir = self.output_dir / repo_name
        else:
            target_dir = Path(target_dir)
            
        # Skip if already exists
        if target_dir.exists():
            self.logger.info(f"Repository already exists at {target_dir}")
            return target_dir
            
        try:
            cmd = ['git', 'clone', '--depth', str(self.clone_depth)]
            
            if branch:
                cmd.extend(['--branch', branch, '--single-branch'])
                
            cmd.extend([repo_url, str(target_dir)])
            
            self.logger.info(f"Cloning repository: {repo_url}")
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            self.logger.info(f"Successfully cloned repository to {target_dir}")
            
            return target_dir
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Error cloning repository {repo_url}: {e}")
            self.logger.error(f"STDERR: {e.stderr}")
            return None
    
    def download_repo_archive(self, repo_url, archive_format='zip'):
        """Download repository as an archive instead of cloning"""
        if 'github.com' in repo_url:
            # Convert github.com URL to API download URL
            parts = repo_url.split('/')
            if len(parts) >= 5:
                owner = parts[-2]
                repo = parts[-1]
                if repo.endswith('.git'):
                    repo = repo[:-4]
                
                download_url = f"https://github.com/{owner}/{repo}/archive/refs/heads/main.{archive_format}"
                filename = f"{repo}-main.{archive_format}"
                
                return self.download_file(download_url, filename)
        
        self.logger.error(f"Unsupported repository URL format: {repo_url}")
        return None
    
    def extract_archive(self, archive_path, target_dir=None):
        """Extract downloaded archive"""
        archive_path = Path(archive_path)
        
        if not archive_path.exists():
            self.logger.error(f"Archive does not exist: {archive_path}")
            return None
            
        if target_dir is None:
            target_dir = archive_path.parent / archive_path.stem
            
        target_dir = Path(target_dir)
        target_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            if archive_path.suffix == '.zip':
                import zipfile
                with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                    zip_ref.extractall(target_dir)
            elif archive_path.suffix in ['.tar', '.gz', '.bz2', '.xz']:
                import tarfile
                with tarfile.open(archive_path, 'r:*') as tar_ref:
                    tar_ref.extractall(target_dir)
            else:
                self.logger.error(f"Unsupported archive format: {archive_path.suffix}")
                return None
                
            self.logger.info(f"Extracted archive to {target_dir}")
            return target_dir
        except Exception as e:
            self.logger.error(f"Error extracting archive {archive_path}: {e}")
            return None

    def download_repo(self, repo_url, repo_name, domain='other', content_type='articles'):
        """Download and save a repository as a zip file in the correct domain/content_type folder."""
        filename = f"{repo_name}.zip"
        target_path = self._get_output_path(domain, content_type, filename)
        target_path.parent.mkdir(parents=True, exist_ok=True)
        
        zip_url = f"{repo_url}/archive/refs/heads/master.zip"
        self.logger.info(f"Downloading {zip_url} to {target_path}")
        try:
            response = self.session.get(zip_url, stream=True)
            response.raise_for_status()
            with open(target_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            self.logger.info(f"Successfully downloaded {target_path}")
            return target_path
        except Exception as e:
            self.logger.error(f"Error downloading {zip_url}: {e}")
            return None

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Collect data from a repository")
    parser.add_argument("--output-dir", required=True, help="Output directory for collected data")
    parser.add_argument("--query", required=True, help="Repository URL or identifier (e.g., 'https://github.com/bitcoin/bitcoin.git')")
    parser.add_argument("--max-items", type=int, default=1, help="Maximum number of repositories to collect (default: 1)")
    parser.add_argument("--clone-depth", type=int, default=1, help="Git clone depth (default: 1)")
    parser.add_argument("--branch", type=str, help="Branch to clone (default: main/master)")
    parser.add_argument("--archive", action="store_true", help="Download as archive instead of cloning")
    parser.add_argument("--extract", action="store_true", help="Extract the downloaded archive (only with --archive)")
    args = parser.parse_args()
    from pathlib import Path
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    collector = RepoCollector(output_dir, clone_depth=args.clone_depth)
    results = []
    if args.archive:
        archive_path = collector.download_repo_archive(args.query)
        if args.extract and archive_path:
            extracted = collector.extract_archive(archive_path)
            if extracted:
                results.append(str(extracted))
        elif archive_path:
            results.append(str(archive_path))
    else:
        # For now, only one repo per call (max_items for future multi-repo support)
        repo_path = collector.clone_repo(args.query, branch=args.branch)
        if repo_path:
            results.append(str(repo_path))
    print(f"Collected {len(results)} repository records. Output dir: {output_dir}")