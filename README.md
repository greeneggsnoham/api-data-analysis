# API Usage Data Tools

Small CLI utility to merge multiple CSV exports into a single file, plus a
small test suite. Intended for cleaning and presenting API usage data exports,
but it
works for any CSVs with compatible structures.

## Features
- Merge CSVs from a folder (optionally recursive, default: `SS`)
- Add `source_file` column to track origin
- Column handling modes: `union`, `intersection`, `strict`
- Configurable delimiter and encoding
- Removes identifying column `project_name` by default (opt out available)
- Removes duplicate rows based on usage identifiers and reports count
- Adds helper columns `start_month` and `end_month` (e.g., `2026-02 February`)
- Optional project filters: `--only-projects` / `--exclude-projects`

## Requirements
- Python 3.10+ (for `|` type hints)
- `pandas`

## Usage
```bash
py merge_files.py -i SS -o merged.csv
py merge_files.py -i data -o out.csv -s -m intersection
py merge_files.py -i data -p "cost_*.csv" -r -d ";" -e "utf-8-sig"
py merge_files.py -i data -o out.csv --keep-identifying-info
py merge_files.py -i data --only-projects ELM,PolicyExplorer,AskEdHelp
py merge_files.py -i data --exclude-projects ELM,PolicyExplorer,AskEdHelp
```

## CLI Options
- `-i`, `--input`: folder containing CSVs (default: `SS`)
- `-o`, `--output`: output CSV path (default: `merged.csv`)
- `-s`, `--add-source`: add a `source_file` column
- `-d`, `--delimiter`: CSV delimiter (default: `,`)
- `-e`, `--encoding`: file encoding (default: `utf-8`)
- `-m`, `--mode`: column handling (`union`, `intersection`, `strict`)
- `-r`, `--recursive`: search input folder recursively
- `-p`, `--pattern`: filename pattern to match (default: `*.csv`)
- `--keep-identifying-info`: keep `project_name` instead of removing it
- `--only-projects`: keep only these project_name values (implies keep)
- `--exclude-projects`: remove these project_name values (implies remove)

## Duplicate Definition
A row is considered a duplicate if all of these fields match:
`start_time`, `end_time`, `start_time_iso`, `end_time_iso`, `amount_value`,
`amount_currency`, `line_item`, `project_id`, `organization_id`.

## Testing
```bash
python -m unittest
```

## Notes
- The repository includes large CSV data files (e.g., `merged.csv`,
  `user email list.csv`). Treat them as inputs/outputs, not source of truth.
- `.gitignore` contains explicit paths for historical exports under `SS/`.
