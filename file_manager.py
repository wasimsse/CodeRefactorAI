import os
import tempfile
import zipfile
import shutil
from pathlib import Path
from typing import Dict, List, Optional
import git
from git.exc import GitCommandError
import magic
import mimetypes
from datetime import datetime

class FileManager:
    def __init__(self, base_dir: Optional[str] = None):
        """Initialize FileManager with a base directory."""
        self.base_dir = base_dir or tempfile.mkdtemp()
        self.files: Dict[str, str] = {}
        
        # Create necessary directories
        self.upload_dir = Path(self.base_dir) / "uploads"
        self.upload_dir.mkdir(exist_ok=True)
        self.cache_dir = Path(self.base_dir) / "cache"
        self.cache_dir.mkdir(exist_ok=True)
        
        # Initialize MIME type detector
        self.mime = magic.Magic(mime=True)
        
        self.temp_dir = tempfile.mkdtemp()
        self.uploaded_files: Dict[str, str] = {}
        self.project_structure: Dict[str, List[str]] = {}
        
    def process_upload(self, uploaded_file) -> List[str]:
        """Process uploaded file and return list of processed file paths."""
        if uploaded_file.name.endswith('.zip'):
            return self._handle_zip_upload(uploaded_file)
        else:
            return [self._handle_single_file_upload(uploaded_file)]

    def read_file(self, file_path: str) -> Optional[str]:
        """Read and return the content of a file."""
        full_path = self.files.get(file_path) or os.path.join(self.base_dir, file_path)
        
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            print(f"Error reading file {file_path}: {str(e)}")
            return None

    def _handle_zip_upload(self, zip_file) -> List[str]:
        """Extract and process ZIP archive."""
        # Create a temporary directory for this upload
        temp_dir = self.upload_dir / f"upload_{os.urandom(8).hex()}"
        temp_dir.mkdir(exist_ok=True)
        
        try:
            # Save zip file temporarily
            zip_path = temp_dir / zip_file.name
            with open(zip_path, 'wb') as f:
                f.write(zip_file.getvalue())
            
            # Extract zip
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)
            
            # Remove zip file
            zip_path.unlink()
            
            # Get all files recursively
            files = []
            for root, _, filenames in os.walk(temp_dir):
                for filename in filenames:
                    file_path = Path(root) / filename
                    if self._is_valid_file(file_path):
                        files.append(str(file_path))
            
            return files
            
        except Exception as e:
            # Clean up on error
            shutil.rmtree(temp_dir, ignore_errors=True)
            raise Exception(f"Error processing ZIP file: {str(e)}")

    def _handle_single_file_upload(self, file) -> str:
        """Process single file upload."""
        try:
            # Create directory for this upload
            upload_path = self.upload_dir / f"file_{os.urandom(8).hex()}"
            upload_path.mkdir(exist_ok=True)
            
            # Save file
            file_path = upload_path / file.name
            with open(file_path, 'wb') as f:
                f.write(file.getvalue())
                
            return str(file_path)
            
        except Exception as e:
            raise Exception(f"Error processing file upload: {str(e)}")

    def _is_valid_file(self, file_path: Path) -> bool:
        """Check if file is valid for processing."""
        try:
            # Check file size
            if file_path.stat().st_size > self.config.MAX_FILE_SIZE:
                return False
                
            # Check file type
            mime_type = self.mime.from_file(str(file_path))
            return mime_type.startswith('text/')
            
        except Exception:
            return False

    def cleanup(self):
        """Clean up temporary files and directories."""
        try:
            # Remove old files from upload directory
            if self.upload_dir.exists():
                shutil.rmtree(self.upload_dir)
                self.upload_dir.mkdir(exist_ok=True)
                
            # Clear cache directory
            if self.cache_dir.exists():
                shutil.rmtree(self.cache_dir)
                self.cache_dir.mkdir(exist_ok=True)
                
            # Clear managed files
            self.files.clear()
        except Exception as e:
            raise Exception(f"Error during cleanup: {str(e)}")

    def get_file_extension(self, file_path: str) -> str:
        """Get the file extension."""
        return os.path.splitext(file_path)[1].lower()

    def get_file_content(self, file_path: str) -> Optional[str]:
        """Get the content of a file."""
        try:
            return self.read_file(file_path)
        except Exception:
            return None

    def save_file_content(self, file_path: str, content: str) -> bool:
        """Save content to a file."""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        except Exception:
            return False

    def handle_file_upload(self, file) -> str:
        """Handle single file upload and return the file path."""
        file_name = file.name
        file_path = os.path.join(self.temp_dir, file_name)
        
        with open(file_path, 'wb') as f:
            f.write(file.getvalue())
            
        self.uploaded_files[file_name] = file_path
        return file_path
        
    def handle_zip_upload(self, zip_file) -> List[str]:
        """Handle ZIP archive upload and return list of extracted file paths."""
        extracted_files = []
        zip_path = os.path.join(self.temp_dir, zip_file.name)
        
        # Save the uploaded ZIP file
        with open(zip_path, 'wb') as f:
            f.write(zip_file.getvalue())
            
        # Extract the ZIP file
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(self.temp_dir)
            
            # Get list of extracted files
            for root, _, files in os.walk(self.temp_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    if self._is_supported_file(file_path):
                        self.uploaded_files[file] = file_path
                        extracted_files.append(file_path)
                        
        return extracted_files
        
    def handle_github_upload(self, repo_url: str) -> List[str]:
        """Handle GitHub repository upload and return list of file paths."""
        try:
            repo_name = repo_url.split('/')[-1].replace('.git', '')
            repo_path = os.path.join(self.temp_dir, repo_name)
            
            # Clone the repository
            git.Repo.clone_from(repo_url, repo_path)
            
            # Get list of files
            files = []
            for root, _, filenames in os.walk(repo_path):
                for filename in filenames:
                    file_path = os.path.join(root, filename)
                    if self._is_supported_file(file_path):
                        relative_path = os.path.relpath(file_path, repo_path)
                        self.uploaded_files[relative_path] = file_path
                        files.append(file_path)
                        
            return files
            
        except GitCommandError as e:
            raise Exception(f"Error cloning repository: {str(e)}")
            
    def get_file_type(self, file_path: str) -> str:
        """Get the MIME type of a file."""
        return self.mime.from_file(file_path)
        
    def is_binary_file(self, file_path: str) -> bool:
        """Check if a file is binary."""
        mime_type = self.get_file_type(file_path)
        return not mime_type.startswith('text/')
        
    def _is_supported_file(self, file_path: str) -> bool:
        """Check if a file is supported for analysis."""
        if self.is_binary_file(file_path):
            return False
            
        ext = self.get_file_extension(file_path)
        supported_extensions = {
            '.py', '.java', '.cpp', '.hpp', '.h',
            '.js', '.jsx', '.ts', '.tsx', '.cs', '.xpp'
        }
        
        return ext in supported_extensions
        
    def get_file_size(self, file_path: str) -> int:
        """Get the size of a file in bytes."""
        return os.path.getsize(file_path)
        
    def get_file_modified_time(self, file_path: str) -> float:
        """Get the last modified time of a file."""
        return os.path.getmtime(file_path)
        
    def get_file_created_time(self, file_path: str) -> float:
        """Get the creation time of a file."""
        return os.path.getctime(file_path)
        
    def get_file_permissions(self, file_path: str) -> str:
        """Get the file permissions."""
        return oct(os.stat(file_path).st_mode)[-3:]
        
    def is_file_readable(self, file_path: str) -> bool:
        """Check if a file is readable."""
        return os.access(file_path, os.R_OK)
        
    def is_file_writable(self, file_path: str) -> bool:
        """Check if a file is writable."""
        return os.access(file_path, os.W_OK)
        
    def is_file_executable(self, file_path: str) -> bool:
        """Check if a file is executable."""
        return os.access(file_path, os.X_OK)
        
    def get_file_owner(self, file_path: str) -> str:
        """Get the owner of a file."""
        return os.stat(file_path).st_uid
        
    def get_file_group(self, file_path: str) -> str:
        """Get the group of a file."""
        return os.stat(file_path).st_gid

    def _handle_single_file_upload(self, uploaded_file) -> str:
        """Handle single file upload and return the saved file path."""
        if not uploaded_file:
            raise ValueError("No file provided")
            
        # Create unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{uploaded_file.name}"
        file_path = self.upload_dir / filename
        
        # Check file size
        if uploaded_file.size > self.config.MAX_FILE_SIZE:
            raise ValueError(f"File size exceeds maximum limit of {self.config.MAX_FILE_SIZE / 1024 / 1024}MB")
            
        # Check file extension
        if Path(uploaded_file.name).suffix not in self.config.ALLOWED_EXTENSIONS:
            raise ValueError(f"File type not allowed. Allowed types: {', '.join(self.config.ALLOWED_EXTENSIONS)}")
            
        # Save file
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
            
        return str(file_path)

    def _handle_zip_upload(self, uploaded_file) -> List[str]:
        """Handle ZIP file upload and return list of extracted file paths."""
        if not uploaded_file:
            raise ValueError("No file provided")
            
        # Check file size
        if uploaded_file.size > self.config.MAX_UPLOAD_SIZE:
            raise ValueError(f"ZIP file size exceeds maximum limit of {self.config.MAX_UPLOAD_SIZE / 1024 / 1024}MB")
            
        # Create temporary directory for extraction
        temp_dir = tempfile.mkdtemp(dir=self.config.TEMP_DIR)
        
        try:
            # Save and extract ZIP file
            zip_path = Path(temp_dir) / uploaded_file.name
            with open(zip_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
                
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)
                
            # Get all valid files
            valid_files = []
            for root, _, files in os.walk(temp_dir):
                for file in files:
                    file_path = Path(root) / file
                    if (file_path.suffix in self.config.ALLOWED_EXTENSIONS and
                        os.path.getsize(file_path) <= self.config.MAX_FILE_SIZE):
                        valid_files.append(str(file_path))
                        
            return valid_files
            
        except Exception as e:
            shutil.rmtree(temp_dir)
            raise Exception(f"Error processing ZIP file: {str(e)}")

    def write_file(self, file_path: str, content: str):
        """Write content to file."""
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)

    def get_file_info(self, file_path: str) -> dict:
        """Get file information including size, type, and last modified time."""
        path = Path(file_path)
        return {
            'name': path.name,
            'size': os.path.getsize(file_path),
            'type': self.mime.from_file(file_path),
            'extension': path.suffix,
            'last_modified': datetime.fromtimestamp(os.path.getmtime(file_path))
        }

    def backup_file(self, file_path: str) -> str:
        """Create a backup of the file and return backup path."""
        path = Path(file_path)
        backup_name = f"{path.stem}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}{path.suffix}"
        backup_path = path.parent / backup_name
        shutil.copy2(file_path, backup_path)
        return str(backup_path)

    def cleanup_temp_files(self):
        """Clean up temporary files and directories."""
        try:
            shutil.rmtree(self.config.TEMP_DIR)
            self.config.TEMP_DIR.mkdir(exist_ok=True)
        except Exception as e:
            print(f"Error cleaning up temporary files: {str(e)}")

    def clone_github_repo(self, repo_url: str, branch: str = "main") -> str:
        """Clone GitHub repository and return path."""
        try:
            repo_name = repo_url.split('/')[-1].replace('.git', '')
            repo_path = self.config.UPLOAD_DIR / repo_name
            
            if repo_path.exists():
                # Update existing repository
                repo = git.Repo(repo_path)
                repo.remotes.origin.pull()
            else:
                # Clone new repository
                git.Repo.clone_from(repo_url, repo_path, branch=branch)
                
            return str(repo_path)
            
        except Exception as e:
            raise Exception(f"Error cloning repository: {str(e)}")

    def get_file_list(self, directory: str, pattern: Optional[str] = None) -> List[str]:
        """Get list of files in directory matching pattern."""
        path = Path(directory)
        if pattern:
            return [str(f) for f in path.rglob(pattern)]
        return [str(f) for f in path.rglob("*") if f.is_file()]

    def create_directory(self, path: str):
        """Create directory if it doesn't exist."""
        Path(path).mkdir(parents=True, exist_ok=True)

    def delete_file(self, file_path: str):
        """Delete file."""
        try:
            os.remove(file_path)
        except Exception as e:
            raise Exception(f"Error deleting file: {str(e)}")

    def move_file(self, source: str, destination: str):
        """Move file from source to destination."""
        try:
            shutil.move(source, destination)
        except Exception as e:
            raise Exception(f"Error moving file: {str(e)}")

    def copy_file(self, source: str, destination: str):
        """Copy file from source to destination."""
        try:
            shutil.copy2(source, destination)
        except Exception as e:
            raise Exception(f"Error copying file: {str(e)}")

    def get_file_hash(self, file_path: str) -> str:
        """Get file hash for comparison."""
        import hashlib
        
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    def save_file(self, file_path: str, content: str) -> str:
        """Save a file with given content and return its path."""
        full_path = os.path.join(self.base_dir, file_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        self.files[file_path] = full_path
        return full_path

    def list_files(self) -> List[str]:
        """Return a list of all managed files."""
        return list(self.files.keys())
    
    def get_file_tree(self) -> Dict:
        """Return a tree structure of all files."""
        tree = {}
        for file_path in self.files:
            parts = file_path.split(os.sep)
            current = tree
            for part in parts[:-1]:
                if part not in current:
                    current[part] = {}
                current = current[part]
            current[parts[-1]] = file_path
        return tree

# Create a default file manager instance
file_manager = FileManager() 