# python
import argparse
from pathlib import Path

VALID_PREFIX_TOKENS = {"i", "v", "h", "r"}

def transform_name(filename: str) -> str | None:
    parts = filename.split("_")
    prefix_len = 0
    for p in parts:
        if p in VALID_PREFIX_TOKENS:
            prefix_len += 1
        else:
            break
    if prefix_len == 0:
        return None
    prefix = parts[:prefix_len]
    rest = parts[prefix_len:]
    if "v" in prefix or "h" in prefix:
        return None
    if "r" in prefix:
        r_index = prefix.index("r")
        new_prefix = prefix[:r_index] + ["h", "r"] + prefix[r_index+1:]
    else:
        new_prefix = prefix + ["h"]
    new_name = "_".join(new_prefix + rest)
    return new_name

def main():
    # Do I really needed to make this? no
    # Will I make it anyway? yes
    parser = argparse.ArgumentParser(description="Converts old prefixes to include the horizontal indicator `h_`.")
    parser.add_argument("--path", "-p", type=str, default=".", help="Directory to process [default: current dir]")
    parser.add_argument("--apply", action="store_true", help="Apply the suggested changes (need rerun) [default: dry-run mode]")
    args = parser.parse_args()

    p = Path(args.path)
    if not p.exists() or not p.is_dir():
        print(f"`{args.path}` it not a valid directory.")
        return

    changes = []
    for file in p.iterdir():
        if not file.is_file():
            continue
        new_name = transform_name(file.name)
        if new_name and new_name != file.name:
            changes.append((file, file.with_name(new_name)))

    if not changes:
        print("No file to rename in this directory.")
        return

    print("Available changes:")
    for old, new in changes:
        print(f"{old.name} -> {new.name}")

    if args.apply:
        for old, new in changes:
            try:
                old.rename(new)
            except Exception as e:
                print(f"Error while renaming {old.name}: {e}")
        print("Files renamed.")
    else:
        print("Dry-run: usa `--apply` per applicare le rinomine.")

if __name__ == "__main__":
    main()
