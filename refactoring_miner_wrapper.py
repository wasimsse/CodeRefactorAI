import os
import subprocess
import json
import tempfile
from pathlib import Path
import shutil

class RefactoringMinerWrapper:
    """
    A simple wrapper for RefactoringMiner that allows integration with the CodeRefactorAI system.
    This wrapper assumes RefactoringMiner is installed as a separate tool and accessible via command line.
    """
    
    def __init__(self, refactoring_miner_path=None):
        """
        Initialize the wrapper with the path to RefactoringMiner.
        
        Args:
            refactoring_miner_path: Path to the RefactoringMiner executable. If None, assumes it's in PATH.
        """
        # TODO: Determine the actual path or command name for RefactoringMiner
        # Path based on user providing the unzipped distribution location
        default_path = "/Users/svm648/CodeRefactorAI_005/RefactoringMiner-3.0.10/bin/RefactoringMiner"
        self.refactoring_miner_command = refactoring_miner_path or default_path
    
    def detect_refactorings_in_file(self, file_path):
        """
        Detect refactorings in a single Java file by comparing it to a dummy previous version.
        NOTE: This is a simplified approach for single file analysis.
        RefactoringMiner is primarily designed for comparing commits.
        
        Args:
            file_path: Path to the Java file to analyze.
            
        Returns:
            List of detected refactorings with their details, or empty list if error/not Java.
        """
        if not file_path or not os.path.exists(file_path) or not file_path.endswith('.java'):
            return []
            
        try:
            # Create a temporary directory for the analysis
            with tempfile.TemporaryDirectory() as temp_dir:
                repo_path = Path(temp_dir) / "temp_repo"
                repo_path.mkdir()
                
                # Initialize a dummy git repository
                subprocess.run(["git", "init"], cwd=repo_path, capture_output=True, text=True, check=True)
                
                # Create a dummy initial commit (e.g., with an empty file)
                dummy_file = repo_path / "dummy.java"
                dummy_file.touch()
                subprocess.run(["git", "add", "."], cwd=repo_path, check=True)
                subprocess.run(["git", "commit", "-m", "Initial dummy commit"], cwd=repo_path, capture_output=True, text=True, check=True)
                initial_commit_sha = subprocess.run(["git", "rev-parse", "HEAD"], cwd=repo_path, capture_output=True, text=True, check=True).stdout.strip()
                
                # Copy the actual file into the repo
                target_file_in_repo = repo_path / os.path.basename(file_path)
                shutil.copy(file_path, target_file_in_repo)
                
                # Create a second commit with the actual file content
                subprocess.run(["git", "add", "."], cwd=repo_path, check=True)
                subprocess.run(["git", "commit", "-m", "Add actual file"], cwd=repo_path, capture_output=True, text=True, check=True)
                second_commit_sha = subprocess.run(["git", "rev-parse", "HEAD"], cwd=repo_path, capture_output=True, text=True, check=True).stdout.strip()

                output_file = Path(temp_dir) / "refactorings.json"
                
                # --- Remove Temporary Debug ---
                # REMOVED: cmd = [self.refactoring_miner_command, "-h"]
                # REMOVED: print(...)
                # REMOVED: result = ...
                # REMOVED: print(...)
                # REMOVED: return []
                # ----------------------------
                
                # >>> Restore Original code below with corrected arguments <<< 
                # Run RefactoringMiner on the second commit (containing the actual file)
                # Use -c <commitSHA> and NO -git flag as per help output
                cmd = [
                    self.refactoring_miner_command, 
                    "-c",   # Analyze a single commit
                    str(repo_path), # Repo path comes after -c
                    second_commit_sha,
                    "-json", str(output_file) 
                ]
                
                print(f"Running command: {' '.join(map(str, cmd))}") # Debug print
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if result.returncode != 0:
                    print(f"Error running RefactoringMiner: {result.stderr}")
                    return []
                
                # Read and parse the output
                if output_file.exists():
                    with open(output_file, 'r') as f:
                        # The output structure might be nested, e.g., under a commit key
                        data = json.load(f)
                        # Adjust parsing based on actual RefactoringMiner JSON output format
                        refactorings_list = []
                        if isinstance(data, dict) and "commits" in data:
                            for commit_info in data["commits"]:
                                refactorings_list.extend(commit_info.get("refactorings", []))
                        elif isinstance(data, list): # Handle cases where it might be a list directly
                             refactorings_list = data
                             
                    return self._format_refactorings(refactorings_list)
                else:
                    print(f"Output file {output_file} not found.")
                    return []
                    
        except subprocess.CalledProcessError as e:
            print(f"Git command error: {e.stderr}")
            return []
        except Exception as e:
            print(f"Error detecting refactorings: {str(e)}")
            return []
    
    def _format_refactorings(self, refactorings_list):
        """
        Format RefactoringMiner results for the UI.
        Adjust based on the actual fields in RefactoringMiner's JSON output.
        
        Args:
            refactorings_list: Raw list of refactoring data from RefactoringMiner.
            
        Returns:
            Formatted list of refactorings.
        """
        formatted = []
        
        for ref in refactorings_list:
            # Extract relevant details - adjust keys based on RefactoringMiner's output
            ref_type = ref.get('type', 'Unknown Type')
            description = ref.get('description', 'No description provided.')
            
            # Location info might be nested or split (left/right side)
            # Example: Combine left/right side info if available
            left_side = ref.get('leftSideLocations', [])
            right_side = ref.get('rightSideLocations', [])
            location_info = "Location info unavailable"
            if left_side:
                 loc = left_side[0] # Take the first location for simplicity
                 location_info = f"{loc.get('filePath', '?')}:L{loc.get('startLine', '?')}-{loc.get('endLine', '?')}"
            elif right_side:
                 loc = right_side[0]
                 location_info = f"{loc.get('filePath', '?')}:L{loc.get('startLine', '?')}-{loc.get('endLine', '?')}"

            formatted.append({
                'type': ref_type,
                'description': description,
                'location': location_info, 
                # Pass other relevant details if needed
                'details': {k: v for k, v in ref.items() if k not in ['type', 'description', 'leftSideLocations', 'rightSideLocations']} 
            })
            
        return formatted 