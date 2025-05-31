#!/usr/bin/env python3
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

def run_command(command, error_message="Command failed"):
    """Run a command and handle its output."""
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
        print(f"✗ {error_message}")
        print(f"Error: {e.stderr}")
        sys.exit(1)

def get_git_changes():
    """Get a summary of changes since last commit."""
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
    for line in modified.split('\n'):
        if not line:
            continue
        status, file = line[:2], line[3:]
        
        # Skip certain files
        if any(file.endswith(ext) for ext in ['.pyc', '.pyo', '.pyd', '.so']):
            continue
        
        if status[0] == 'M':  # Modified file
            # Get summary of changes
            diff = run_command(
                f'git diff --unified=0 "{file}"',
                f"Failed to get diff for {file}"
            )
            changes.append(f"Modified {file}")
            
        elif status[0] == 'A':  # Added file
            changes.append(f"Added {file}")
            
        elif status[0] == 'D':  # Deleted file
            changes.append(f"Deleted {file}")
            
        elif status[0] == 'R':  # Renamed file
            old, new = file.split(' -> ')
            changes.append(f"Renamed {old} to {new}")
    
    return changes

def main():
    # 1. Generate commit message
    print("Analyzing changes...")
    changes = get_git_changes()
    
    if not changes:
        print("No changes detected.")
        return
    
    # Create commit message
    date = datetime.now().strftime("%Y-%m-%d %H:%M")
    commit_msg = f"Update {date}\n\nChanges:\n" + "\n".join(f"- {change}" for change in changes)
    
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

if __name__ == "__main__":
    main()