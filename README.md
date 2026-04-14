# tak-shadowfleet-id from https://github.com/sgofferj/tak-shadowfleet-id
#
# Copyright Stefan Gofferje
#
# Licensed under the Gnu General Public License Version 3 or higher (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at https://www.gnu.org/licenses/gpl-3.0.en.html

# Description
`tak-shadowfleet-id` is a Python-based scraper designed to aggregate and deduplicate data from multiple OSINT and official maritime sanction sources to identify "shadow fleet" vessels. The output is a JSON dataset (`shadowfleet.json`) suitable for integration into TAK (Team Awareness Kit) environments.

The dataset includes IMO numbers, MMSIs, vessel names, types, flags, and CoT (Cursor on Target) types.

# Configuration
The application can be configured via command-line arguments.

| Argument | Description | Default |
|----------|-------------|---------|
| `--nogit` | Skip pushing the results to a Git repository | `False` |

### Source Data
The scraper currently fetches data from:
- **OpenSanctions**: Simple CSV target dataset.
- **UK Sanctions List**: Official FCDO maritime sanctions.

# Container use
A multi-arch Docker image is available for both AMD64 and ARM64.

### Build
To build the image locally:
```bash
docker build -t tak-shadowfleet-id:latest .
```

### Run
To run the scraper inside a container:
```bash
docker run --rm -v $(pwd):/app tak-shadowfleet-id:latest
```
Note: To persist the `shadowfleet.json` file, mount the current directory as `/app`.

# Installation
This project uses [Poetry](https://python-poetry.org/) for dependency management.

### Prerequisites
- Python >= 3.12
- Poetry

### Setup
1. Clone the repository.
2. Install dependencies:
   ```bash
   poetry install
   ```
3. Run the scraper:
   ```bash
   poetry run tak-shadowfleet-id
   ```

# GitHub Actions (Scheduled CI)
This project is configured with GitHub Actions to run the scraper daily at midnight. The workflow:
1. Runs linting and type checking (`black`, `mypy`, `pylint`).
2. Executes the scraper.
3. Automatically commits and pushes changes to `shadowfleet.json` back to the repository if updates are found.
4. Performs a multi-arch Docker build test.

# License
Copyright Stefan Gofferje.
Software licensed under the Gnu General Public License Version 3 or higher.
Dataset produced by this tool is licensed under [CC-BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).
