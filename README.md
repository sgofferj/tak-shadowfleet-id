> [!CAUTION]
> The dataset provided by this tool is collected automatically from third parties. There is no guarantee that the dataset provided by this tool is up-to-date or correct. I am not responsible for incorrect or outdated data.
> The classification of vessels under international sanctions with the CoT type "suspicious" is protected by Freedom of Opinion and Free Speech.

> [!IMPORTANT]
> The dataset is licensed under [CC-BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/)
> Because it inherits the strictest license from all sources which currently is CC-BY-NC 4.0 (see below).
> Please note that this is the Creative Commons license with the **NONCOMMERCIAL** clause.


# Description
`tak-shadowfleet-id` is a Python-based data collector designed to aggregate and deduplicate data from multiple OSINT and official maritime sanction sources to identify "shadow fleet" vessels. The output is a JSON dataset (`shadowfleet.json`) suitable for integration into TAK (Team Awareness Kit) environments.

The dataset includes IMO numbers, MMSIs, vessel names, types, flags, and CoT (Cursor on Target) types.

## Attribution

The data collector currently fetches data the following sources:

### OpenSanctions
[https://www.opensanctions.org](https://www.opensanctions.org)

- Simple CSV target dataset, **License:** [CC-BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/)

### UK FCDO Sanctions List
[https://www.gov.uk/government/publications/the-uk-sanctions-list](https://www.gov.uk/government/publications/the-uk-sanctions-list)

- CSV list, **License:** [Open Government Licence v3.0](https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/)

# Container use
A multi-arch Docker image is available for both AMD64 and ARM64.

### Build
To build the image locally:
```bash
docker build -t tak-shadowfleet-id:latest .
```

### Run
To run the data collector inside a container:
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
3. Run the data collector:
   ```bash
   poetry run tak-shadowfleet-id
   ```

# GitHub Actions (Scheduled CI)
This project is configured with GitHub Actions to run the data collector daily at midnight. The workflow:
1. Runs linting and type checking (`black`, `mypy`, `pylint`).
2. Executes the data collector.
3. Automatically commits and pushes changes to `shadowfleet.json` back to the repository if updates are found.
4. Performs a multi-arch Docker build test.

# License for the code
Copyright Stefan Gofferje.
Software licensed under the Gnu General Public License Version 3 or higher.

# License for the dataset
The dataset produced by this tool inherits the strictest license from all sources which currently is CC-BY-NC 4.0. Please note that this is the Creative Commons license with the **NONCOMMERCIAL** clause.
