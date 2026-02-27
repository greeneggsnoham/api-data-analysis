# API Usage Data Tools

Small CLI utility to merge multiple CSV exports into a single file, plus a
small test suite. Intended for cleaning and presenting API usage data exports,
but it
works for any CSVs with compatible structures.

## Features
- Merge CSVs from a folder (optionally recursive)
- Add `source_file` column to track origin
- Column handling modes: `union`, `intersection`, `strict`
- Configurable delimiter and encoding
- Removes identifying column `project_name` by default (opt out available)

## Requirements
- Python 3.10+ (for `|` type hints)
- `pandas`

## Usage
```bash
python merge_files.py -i . -o merged.csv
python merge_files.py -i data -o out.csv -s -m intersection
python merge_files.py -i data -p "cost_*.csv" -r -d ";" -e "utf-8-sig"
python merge_files.py -i data -o out.csv --keep-identifying-info
```

## CLI Options
- `-i`, `--input`: folder containing CSVs (default: current folder)
- `-o`, `--output`: output CSV path (default: `merged.csv`)
- `-s`, `--add-source`: add a `source_file` column
- `-d`, `--delimiter`: CSV delimiter (default: `,`)
- `-e`, `--encoding`: file encoding (default: `utf-8`)
- `-m`, `--mode`: column handling (`union`, `intersection`, `strict`)
- `-r`, `--recursive`: search input folder recursively
- `-p`, `--pattern`: filename pattern to match (default: `*.csv`)
- `--keep-identifying-info`: keep `project_name` instead of removing it

## Testing
```bash
python -m unittest
```

## Notes
- The repository includes large CSV data files (e.g., `merged.csv`,
  `user email list.csv`). Treat them as inputs/outputs, not source of truth.
- `.gitignore` contains explicit paths for historical exports under `SS/`.
