#!/usr/bin/env python3
import os
import subprocess
import sys
import traceback
from datetime import datetime
from pathlib import Path
import platform
import shutil
import json

class DeployError(Exception):
    """Custom exception for deployment errors"""
    def __init__(self, message, command=None, stdout=None, stderr=None, details=None):
        super().__init__(message)
        self.command = command
        self.stdout = stdout
        self.stderr = stderr
        self.details = details or {}

def get_system_info():
    """Get relevant system information for debugging"""
    return {
        "platform": platform.platform(),
        "python_version": sys.version,
        "cwd": os.getcwd(),
        "path_sep": os.path.sep,
        "docker_installed": shutil.which("docker") is not None,
        "git_installed": shutil.which("git") is not None,
        "env_vars": {
            k: v for k, v in os.environ.items() 
            if k.lower() in ['path', 'python_path', 'virtual_env', 'docker_host']
        }
    }

def log_error(error, error_type="Error", exit_code=1):
    """Log error details in a structured way"""
    error_log = {
        "timestamp": datetime.now().isoformat(),
        "type": error_type,
        "message": str(error),
        "system_info": get_system_info()
    }
    
    if isinstance(error, DeployError):
        error_log.update({
            "command": error.command,
            "stdout": error.stdout,
            "stderr": error.stderr,
            "details": error.details
        })
    else:
        error_log["traceback"] = traceback.format_exc()

    # Create logs directory if it doesn't exist
    log_dir = Path("deploy_logs")
    log_dir.mkdir(exist_ok=True)
    
    # Save error log to file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"deploy_error_{timestamp}.json"
    with open(log_file, 'w', encoding='utf-8') as f:
        json.dump(error_log, f, indent=2, ensure_ascii=False)

    print(f"\n{'='*50}")
    print(f"{error_type} Details:")
    print(f"{'='*50}")
    print(f"Message: {error}")
    if isinstance(error, DeployError):
        if error.command:
            print(f"\nCommand: {error.command}")
        if error.stdout:
            print(f"\nCommand Output:\n{error.stdout}")
        if error.stderr:
            print(f"\nError Output:\n{error.stderr}")
        if error.details:
            print("\nAdditional Details:")
            for k, v in error.details.items():
                print(f"{k}: {v}")
    print(f"\nError log saved to: {log_file}")
    print(f"{'='*50}")
    
    if exit_code is not None:
        sys.exit(exit_code)

def run_command(command, error_message="Command failed"):
    """Run a command and handle its output with detailed error reporting."""
    try:
        result = subprocess.run(
            command,
            check=True,
            text=True,
            capture_output=True,
            shell=True
        )
        print(f"✓ {command}")
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        raise DeployError(
            error_message,
            command=command,
            stdout=e.stdout,
            stderr=e.stderr,
            details={
                "return_code": e.returncode,
                "env": dict(os.environ),
            }
        )
    except Exception as e:
        raise DeployError(
            f"Unexpected error running command: {str(e)}",
            command=command,
            details={"exception_type": type(e).__name__}
        )

def get_git_changes():
    """Get a summary of changes since last commit with detailed error handling."""
    try:
        # Get modified files
        modified = run_command(
            "git status --porcelain",
            "Failed to get git status"
        )
        
        if not modified:
            print("No changes to commit!")
            sys.exit(0)
        
        # Get detailed changes for each file
        changes = []
        skipped_files = []
        diff_errors = []
        
        for line in modified.split('\n'):
            if not line:
                continue
            status, filepath = line[:2], line[3:].strip()
            
            # Skip certain files
            if any(filepath.endswith(ext) for ext in ['.pyc', '.pyo', '.pyd', '.so']):
                skipped_files.append(filepath)
                continue
            
            # Convert path to use forward slashes for git
            git_path = filepath.replace('\\', '/')
            
            if status[0] == 'M':  # Modified file
                try:
                    # Get summary of changes
                    diff = run_command(
                        f'git diff --unified=0 "{git_path}"',
                        f"Failed to get diff for {filepath}"
                    )
                    changes.append({
                        "type": "modified",
                        "file": filepath,
                        "diff_available": True
                    })
                except Exception as e:
                    diff_errors.append({
                        "file": filepath,
                        "error": str(e)
                    })
                    changes.append({
                        "type": "modified",
                        "file": filepath,
                        "diff_available": False,
                        "error": str(e)
                    })
                
            elif status[0] == 'A':  # Added file
                changes.append({
                    "type": "added",
                    "file": filepath
                })
                
            elif status[0] == 'D':  # Deleted file
                changes.append({
                    "type": "deleted",
                    "file": filepath
                })
                
            elif status[0] == 'R':  # Renamed file
                old, new = filepath.split(' -> ')
                changes.append({
                    "type": "renamed",
                    "old_file": old,
                    "new_file": new
                })
        
        # Log summary information
        if skipped_files:
            print("\nSkipped files:")
            for file in skipped_files:
                print(f"- {file}")
        
        if diff_errors:
            print("\nDiff errors:")
            for error in diff_errors:
                print(f"- {error['file']}: {error['error']}")
        
        return changes

    except Exception as e:
        raise DeployError(
            "Failed to analyze git changes",
            details={
                "exception": str(e),
                "git_dir_exists": os.path.exists(".git"),
                "is_git_repo": os.path.exists(".git/config")
            }
        )

def main():
    try:
        # 1. Generate commit message
        print("Analyzing changes...")
        changes = get_git_changes()
        
        if not changes:
            print("No changes detected.")
            return
        
        # Create commit message with detailed changes
        date = datetime.now().strftime("%Y-%m-%d %H:%M")
        commit_lines = [f"Update {date}", ""]
        
        # Group changes by type
        changes_by_type = {}
        for change in changes:
            change_type = change["type"]
            if change_type not in changes_by_type:
                changes_by_type[change_type] = []
            changes_by_type[change_type].append(change)
        
        # Format changes in commit message
        for change_type, type_changes in changes_by_type.items():
            commit_lines.append(f"{change_type.title()} files:")
            for change in type_changes:
                if change_type == "renamed":
                    commit_lines.append(f"- {change['old_file']} -> {change['new_file']}")
                else:
                    commit_lines.append(f"- {change['file']}")
                    if change_type == "modified" and not change.get("diff_available"):
                        commit_lines.append(f"  (diff unavailable: {change.get('error', 'unknown error')})")
            commit_lines.append("")
        
        commit_msg = "\n".join(commit_lines)
        
        # Show the commit message and ask for confirmation
        print("\nProposed commit message:")
        print("-" * 50)
        print(commit_msg)
        print("-" * 50)
        
        response = input("\nProceed with this commit message? (Y/n/e to edit): ").lower()
        
        if response == 'n':
            print("Operation cancelled.")
            return
        elif response == 'e':
            # Create temporary file with commit message
            temp_file = Path("temp_commit_msg.txt")
            temp_file.write_text(commit_msg)
            
            # Open editor
            editor = os.environ.get('EDITOR', 'vim')
            subprocess.call([editor, temp_file])
            
            # Read edited message
            commit_msg = temp_file.read_text()
            temp_file.unlink()  # Delete temporary file
        
        # 2. Git add
        print("\nStaging changes...")
        run_command("git add .", "Failed to stage changes")
        
        # 3. Git commit
        print("\nCommitting changes...")
        run_command(
            f'git commit -m "{commit_msg}"',
            "Failed to commit changes"
        )
        
        # 4. Git push
        print("\nPushing to remote...")
        run_command("git push", "Failed to push changes")
        
        # 5. Docker compose
        print("\nRebuilding and starting Docker containers...")
        run_command(
            "docker-compose up -d --build",
            "Failed to rebuild and start Docker containers"
        )
        
        print("\n✓ All operations completed successfully!")

    except DeployError as e:
        log_error(e, "Deployment Error")
    except Exception as e:
        log_error(e, "Unexpected Error")

if __name__ == "__main__":
    main()