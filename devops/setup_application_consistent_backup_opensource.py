#!/usr/bin/env python3
"""
Setup script for Azure VM application-consistent backup.
This script creates the necessary files in /etc/azure directory with proper permissions.

Open Source Version - Safe for public distribution
"""

import os
import stat
import sys

# File contents embedded in the script
PRE_BACKUP_CONTENT = '''#!/bin/bash

# Define logging function
log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | sudo tee -a /var/log/azure-backup.log > /dev/null
}

# Pause the application before backup
log_message "Pre-backup script started - pausing application"

# Example: Stop your application service
# Replace 'your-app-service' with your actual service name
SERVICE_NAME="your-app-service"

# Check if the service is running before attempting to stop it
if systemctl is-active --quiet $SERVICE_NAME; then
    sudo systemctl stop $SERVICE_NAME
    if [ $? -eq 0 ]; then
        log_message "Successfully stopped $SERVICE_NAME"
    else
        log_message "WARNING: Failed to stop $SERVICE_NAME"
        # Continue anyway, as we don't want to fail the backup
    fi
else
    log_message "$SERVICE_NAME was not running, nothing to stop"
fi

# Additional application-specific commands can be added here
# Examples:
# - Stop database connections
# - Flush application caches
# - Quiesce file systems

# Flush any filesystem buffers
sync

log_message "Pre-backup script completed"
exit 0
'''

POST_BACKUP_CONTENT = '''#!/bin/bash

# Define logging function
log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | sudo tee -a /var/log/azure-backup.log > /dev/null
}

# Resume the application after backup
log_message "Post-backup script started - resuming application"

# Example: Start your application service
# Replace 'your-app-service' with your actual service name
SERVICE_NAME="your-app-service"

# Start the service
sudo systemctl start $SERVICE_NAME
if [ $? -eq 0 ]; then
    log_message "Successfully started $SERVICE_NAME"
else
    log_message "ERROR: Failed to start $SERVICE_NAME"
    # We don't exit with error as we don't want to mark the backup as failed
    # but this should be investigated
fi

# Additional application-specific commands can be added here
# Examples:
# - Restart database connections
# - Reload application configurations
# - Verify application health

log_message "Post-backup script completed"
exit 0
'''

CONFIG_CONTENT = '''{
  "pluginName": "ScriptRunner",
  "preScriptLocation": "/etc/azure/pre_backup.sh",
  "postScriptLocation": "/etc/azure/post_backup.sh",
  "preScriptParams": ["", ""],
  "postScriptParams": ["", ""],
  "preScriptNoOfRetries": 0,
  "postScriptNoOfRetries": 0,
  "timeoutInSeconds": 30,
  "continueBackupOnFailure": true,
  "fsFreezeEnabled": true
}
'''

def create_directory_if_not_exists(directory):
    """Create directory if it doesn't exist."""
    try:
        os.makedirs(directory, exist_ok=True)
        print(f"Directory {directory} created or already exists.")
    except Exception as e:
        print(f"Error creating directory {directory}: {e}")
        return False
    return True

def create_file_with_content_and_permissions(file_path, content, permissions):
    """Create file with content and set permissions."""
    try:
        # Write content to file
        with open(file_path, 'w') as f:
            f.write(content)
        print(f"Created {file_path}")
        
        # Set permissions
        os.chmod(file_path, permissions)
        print(f"Set permissions {oct(permissions)} on {file_path}")
        
        return True
    except Exception as e:
        print(f"Error creating {file_path}: {e}")
        return False

def main():
    """Main function to setup application-consistent backup files."""
    # Check if running as root (only on Unix-like systems)
    if hasattr(os, 'geteuid') and os.geteuid() != 0:
        print("This script must be run as root (sudo).")
        print("Usage: sudo python3 setup_application_consistent_backup.py")
        sys.exit(1)
    
    # Define paths
    azure_dir = "/etc/azure"
    
    # Destination files
    pre_backup_dest = os.path.join(azure_dir, "pre_backup.sh")
    post_backup_dest = os.path.join(azure_dir, "post_backup.sh")
    config_dest = os.path.join(azure_dir, "VMSnapshotScriptPluginConfig.json")
    
    print("Starting Azure VM application-consistent backup setup...")
    print("")
    print("IMPORTANT: Before using this script, please:")
    print("1. Replace 'your-app-service' in the scripts with your actual service name")
    print("2. Add any additional application-specific commands as needed")
    print("3. Test the scripts manually before relying on them for backups")
    print("")
    
    # Create /etc/azure directory
    if not create_directory_if_not_exists(azure_dir):
        sys.exit(1)
    
    # Create files with appropriate permissions
    success = True
    
    # VMSnapshotScriptPluginConfig.json - Permission 600 (read/write for owner only)
    if not create_file_with_content_and_permissions(config_dest, CONFIG_CONTENT, stat.S_IRUSR | stat.S_IWUSR):
        success = False
    
    # pre_backup.sh - Permission 700 (read/write/execute for owner only)
    if not create_file_with_content_and_permissions(pre_backup_dest, PRE_BACKUP_CONTENT, stat.S_IRWXU):
        success = False
    
    # post_backup.sh - Permission 700 (read/write/execute for owner only)
    if not create_file_with_content_and_permissions(post_backup_dest, POST_BACKUP_CONTENT, stat.S_IRWXU):
        success = False
    
    if success:
        print("\nSetup completed successfully!")
        print("Files created in /etc/azure:")
        print(f"  - {config_dest} (permissions: 600)")
        print(f"  - {pre_backup_dest} (permissions: 700)")
        print(f"  - {post_backup_dest} (permissions: 700)")
        print("\nNext steps:")
        print("1. Edit the script files to replace 'your-app-service' with your actual service")
        print("2. Add any additional application-specific commands")
        print("3. Test the scripts manually: sudo /etc/azure/pre_backup.sh && sudo /etc/azure/post_backup.sh")
        print("4. Monitor backup logs: /var/log/azure/Microsoft.Azure.RecoveryServices.VMSnapshotLinux/extension.log")
        print("\nAzure VM application-consistent backup is now configured.")
    else:
        print("\nSetup failed. Please check the errors above.")
        sys.exit(1)

if __name__ == "__main__":
    main()