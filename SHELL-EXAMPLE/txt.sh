#!/bin/bash

for file in *.txt

do
    if [ -f "$file" ]; then
        echo "Processing file: $file"
        # Add your processing logic here
    else
        echo "No .txt files found in the current directory."
    fi
    done