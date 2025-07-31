#!/bin/bash

folder1="AI/src/ground_truth/vision/dreamy"
folder2="AI/src/ground_truth/abstraction/dreamy"

for file1 in "$folder1"/*; do
    filename=$(basename "$file1")
    file2="$folder2/$filename"

    # Check if corresponding file exists
    if [[ ! -f "$file2" ]]; then
        echo "Missing in second folder: $filename"
        continue
    fi

    # Compare line counts
    lines1=$(wc -l < "$file1")
    lines2=$(wc -l < "$file2")

    if [[ "$lines1" -ne "$lines2" ]]; then
        echo "$filename lines mismatch"
        continue
    fi

    # Compare .png string presence line by line
    fail=0
    paste "$file1" "$file2" | while IFS=$'\t' read -r line1 line2; do
        # Extract strings with only letters and underscores, possibly followed by .png
        word1=$(echo "$line1" | grep -oE '[a-zA-Z_]+(\.png)?' | sed 's/\.png$//' | head -n1)
        word2=$(echo "$line2" | grep -oE '[a-zA-Z_]+(\.png)?' | sed 's/\.png$//' | head -n1)

        if [ "$word1" != "$word2" ]; then
            fail=1
            break
        fi
    done

    if [[ "$fail" -eq 1 ]]; then
        echo "$filename mismatches on some label"
    fi
done
