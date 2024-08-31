#!/bin/bash

# Check if source and destination directories are provided
if [ $# -ne 2 ]; then
    echo "Usage: $0 <source_directory> <destination_directory>"
    exit 1
fi

source_dir="$1"
dest_dir="$2"

# Check if source directory exists
if [ ! -d "$source_dir" ]; then
    echo "Error: Source directory does not exist."
    exit 1
fi

# Create destination directory if it doesn't exist
mkdir -p "$dest_dir"

# Loop through directories in the source directory
for dir in "$source_dir"/*/ ; do
    if [ -d "$dir" ]; then
        dir_name=$(basename "$dir")
        mkdir -p "$dest_dir/$dir_name"
        echo "Created directory: $dest_dir/$dir_name"
    fi
done

echo "Directory name copying completed."