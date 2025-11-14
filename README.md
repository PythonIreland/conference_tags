# Conference Tags

Generate printable, CMYK-safe conference name badges from Tito tickets and Sessionize speakers data.

## Requirements

- Python 3.12+
- [Task](https://taskfile.dev/) (task runner)
- A Tito API token
- Required fonts (see [Fonts](#fonts) section)

## Setup

### 1. Installing dependencies
We are transitioning from `requirements.txt` to `pyproject.toml` managed by `uv`. Use one of the following methods.

### Option A — pip with requirements.txt (current)
Use this today.

```bash
python -m venv .venv
# bash/zsh:
source .venv/bin/activate
# fish:
# source .venv/bin/activate.fish
pip install -U pip
pip install -r requirements.txt
```

### Option B — uv with pyproject.toml (future/preferred)
Once dependencies are declared in `pyproject.toml`, `uv` will manage the environment and installs.

1) Install uv (choose one):
- Homebrew: `brew install uv`
- pipx: `pipx install uv`

2) Create the virtual environment and install:

```bash
uv sync
```

If you want to use `uv` today with the existing requirements file:

```bash
uv venv
# bash/zsh:
source .venv/bin/activate
# fish:
# source .venv/bin/activate.fish
uv pip install -r requirements.txt
```

### 2. Configuration

#### API Token

Add your Tito API token to `.secret.toml`:

```toml
TITO_TOKEN = "your_token_here"
```

You can find your API key by signing in at https://api.tito.io.

#### Settings

Project settings live in `settings.toml`. Adjust values there to match your event and output needs.

### 3. Fonts
Place required TTF files in the `./fonts` directory.

- **UbuntuMono-R.ttf** - Used because it clearly distinguishes 0 vs O, and 1 vs l vs I
- **Bree font** - Licensed font (not free). The TTF files are stored in our Google Drive

## Usage

### Quick Start - Automated Workflow

If you have the Sessionize Excel file ready, you can run the complete workflow with a single command:

```bash
task workflow:complete
```

This will automatically:
1. Convert the Sessionize Excel file to JSON
2. Download tickets from Tito
3. Generate the badges PDF

**Prerequisites:**
- `pycon-ireland-YYYY-sessionize.xlsx` must exist in the current directory
- `.secret.toml` configured with your Tito API token

### Manual Step-by-Step Process

If you prefer to run each step individually, follow these steps:

#### Step 1: Download Speakers from Sessionize

1. Go to the Sessionize website and select your event (e.g., **PyCon Ireland 2025**)
2. Navigate to the **Export** section
3. In the **Session and Speaker** area, download the **Accepted** sessions file
   - This ensures you only get accepted sessions without unnecessary noise
4. Save the downloaded Excel file as `pycon-ireland-YYYY-sessionize.xlsx` (replace YYYY with the current year)

**Direct URL:** https://sessionize.com/app/organizer/export/excel/19814/Accepted_sessions

The Excel file will contain multiple sheets with session and speaker information ans save it as `pycon-ireland-YYYY-sessionize.xlsx` (replace YYYY with the current year).

#### Step 2: Convert Sessionize Data to JSON

The Excel file from Sessionize needs to be converted to JSON format. This is done using the `convert-sessionize-to-json.py` script, which extracts the necessary information from the multiple sheets and validates the output structure.

Run the conversion:

```bash
task sessionize:convert
```

This command:
- Takes the `pycon-ireland-YYYY-sessionize.xlsx` file as input
- Extracts speaker and session information from the Excel sheets
- Outputs a validated `pycon-ireland-YYYY-speakers.json` file

#### Step 3: Download Tickets from Tito

Download the list of sold tickets for the current event from Tito. This uses the `build_badge.py` script with the `download-tickets` command.

Run the download:

```bash
task tito:download:tickets
```

This command:
- Connects to the Tito API using your configured token
- Downloads all ticket data for the current event (defined by the YEAR variable in `Taskfile.yaml`)
- Creates a `pycon-ireland-YYYY-tickets.json` file with all attendee information

#### Step 4: Generate Badge PDF

Generate the print-ready PDF with all badges. This uses the `build_badge.py` script with the `build` command, combining both the tickets and speakers data.

```bash
task badges:generate
```

This command:
- Automatically removes any existing `pycon-ireland-YYYY-badges.pdf` file
- Takes the `pycon-ireland-YYYY-tickets.json` file (attendee data)
- Takes the `pycon-ireland-YYYY-speakers.json` file (speaker data)
- Generates a `pycon-ireland-YYYY-badges.pdf` file with all badges
- Uses CMYK colors suitable for professional printing
- Applies the configured fonts and styling

#### Step 5: Generate Blank Badges (Optional)

For last-minute attendees or walk-ins at the conference, you can generate blank badges that can be filled in by hand.

```bash
task badges:blank
```

This command generates a single blank badge by default. To generate multiple blank badges, use:

```bash
task badges:blank -- --limit 5
```

This command:
- Generates `blank-tickets.pdf` with the specified number of blank badges
- Uses the same styling and layout as regular badges
- Creates badges without attendee names or QR codes
- Perfect for on-site registrations or replacements

## Available Tasks

The `Taskfile.yaml` provides convenient commands for all operations. Use `task --list` to see all available tasks, or `task --summary <task-name>` for detailed information about a specific task.

### Workflow & Utilities
- `task workflow:complete` - **Complete automated workflow** (convert → download → generate)
- `task check` - Verify environment setup and required tools
- `task show` - Display current YEAR and EVENT variables
- `task show:files` - List all generated files for current event
- `task clean` - Remove all generated files for current event
- `task clean:all` - Remove all generated files for all years (with confirmation)

### Environment Management
- `task environment:create` - Create Python virtual environment
- `task environment:install` - Install dependencies (with precondition check)
- `task environment:drop` - Remove virtual environment
- `task environment:reset` - Reset environment (drop + create + install)

### Code Quality
- `task format:ruff` - Format all Python files with ruff

### Data Download (Tito)
- `task tito:download:tickets` - Download tickets for current event → `pycon-ireland-YYYY-tickets.json`
- `task tito:download:all` - Download tickets from all previous years
- `task tito:download:checkins` - Download check-in data → `checkins.json`
- `task tito:count:api` - Count tickets via Tito API

### Data Processing
- `task sessionize:convert` - Convert Sessionize Excel to JSON (with validation)
- `task badges:generate` - Generate badge PDF (with precondition checks)
- `task badges:blank` - Generate blank badges for last-minute attendees → `blank-tickets.pdf`
- `task report:generate` - Generate Excel report merging Tito and Sessionize data

### Analysis & Reporting
- `task tickets:count` - Count tickets from local JSON file (requires jq)
- `task tickets:graph` - Generate ticket graphs
- `task tickets:update-references` - Update ticket references from mapping file → `pycon-ireland-YYYY-tickets-updated.json`
- `task tshirts:distribution:current` - T-shirt size distribution for current year
- `task tshirts:distribution:all` - T-shirt size distribution for all years

## Useful Tips

### Checking Your Setup

Before generating badges, verify your environment is properly configured:

```bash
task check
```

This will check for:
- `.secret.toml` configuration file
- Virtual environment
- Required fonts (UbuntuMono-R.ttf)
- External tools (jq, httpie)

### Viewing Generated Files

To see which files exist for the current event:

```bash
task show:files
```

### Getting Detailed Task Information

To see detailed information about any task, including prerequisites and outputs:

```bash
task --summary <task-name>
```

Example:
```bash
task --summary badges:generate
```

### Cleaning Up

To remove generated files for the current event:

```bash
task clean
```

To remove ALL generated files across all years:

```bash
task clean:all
```

### Formatting Code

To format all Python files in the project with ruff:

```bash
task format:ruff
```

To format a specific file:

```bash
task format:ruff -- build_badge.py
```

Ruff is a fast Python linter and formatter that ensures consistent code style across the project.

### Email Mapping for Speakers

Sometimes speakers register on Sessionize with a different email address than the one they use to purchase tickets on Tito. This creates a mismatch when trying to identify which speakers have tickets.

To solve this, create an `emails.mapping.csv` file to map between the two email addresses:

#### Format

```csv
tito_email,sessionize_email
john.doe@company.com,john.personal@gmail.com
jane.smith@work.com,jane@example.org
```

#### Example Use Cases

**Problem:** A speaker registered on Sessionize with `speaker@personal.com` but bought their ticket with `speaker@work.com`.

**Solution:** Add a mapping:
```csv
tito_email,sessionize_email
speaker@work.com,speaker@personal.com
```

#### How It Works

1. The `badges:generate` and `report:generate` tasks automatically load `emails.mapping.csv` if it exists
2. When matching speakers to tickets, the system will:
   - First check for direct email matches
   - Then apply mappings from the CSV file
   - Mark the person as a speaker if either email matches

#### When to Use

- Speaker uses different emails on Sessionize vs Tito
- Speaker changed email addresses between registration and ticket purchase
- Corporate vs personal email situations
- Misspelled emails that need correction

#### Location

Place the `emails.mapping.csv` file in the root directory of the project (same location as `Taskfile.yaml`).

**Template:** A template file `emails.mapping.csv.example` is provided in the repository. Copy it to `emails.mapping.csv` and add your mappings.

```bash
cp emails.mapping.csv.example emails.mapping.csv
# Then edit emails.mapping.csv with your actual mappings
```

**Note:** The actual `emails.mapping.csv` file is automatically ignored by git (see `.gitignore`) as it may contain personal information.

### Updating Ticket References

Sometimes you need to modify ticket reference codes (the unique identifiers like "BBGQ-1"). This is useful for:
- Anonymizing ticket data for testing or demonstrations
- Creating custom reference codes for internal use
- Migrating between different reference systems

#### Creating a Mapping File

Create a `reference-mapping.json` file in the project root with the old and new reference codes:

```json
{
    "BBGQ-1": "KARA-TE",
    "XYZA-2": "JUDO-42",
    "TEST-3": "DEMO-99"
}
```

#### Using the Task Command

```bash
# Preview changes without modifying files
task tickets:update-references -- --dry-run

# Apply the changes
task tickets:update-references
```

This will:
1. Read your tickets from `pycon-ireland-YYYY-tickets.json`
2. Apply the reference mappings from `reference-mapping.json`
3. Output the updated tickets to `pycon-ireland-YYYY-tickets-updated.json`

#### Direct Script Usage

You can also use the script directly:

```bash
# Update references
python update-ticket-references.py \
    pycon-ireland-2025-tickets.json \
    reference-mapping.json \
    pycon-ireland-2025-tickets-updated.json

# Preview changes (dry run)
python update-ticket-references.py \
    pycon-ireland-2025-tickets.json \
    reference-mapping.json \
    pycon-ireland-2025-tickets-updated.json \
    --dry-run
```

**Note:** The `reference-mapping.json` file is automatically ignored by git to prevent accidental commits of potentially sensitive mappings. An example template is provided in `reference-mapping.example.json`.

## Technical Details

### Color and Printing

All colors used for PDF generation are CMYK-based, ensuring compatibility with professional printing services. Color definitions are in the badge-building code.

### Smart Rebuilds

Task tracks file dependencies automatically. If source files haven't changed, tasks won't re-run unnecessarily. This is especially useful for `badges:generate` which checks if tickets or speakers JSON files have been updated.

### Error Handling

All critical tasks include precondition checks. If a required file is missing, you'll get a clear error message indicating which command to run first.

### Scripts Overview

The project includes several Python scripts:

- **`convert-sessionize-to-json.py`** - Converts Sessionize Excel exports to JSON format
- **`build_badge.py`** - Main script with subcommands:
  - `download-tickets` - Downloads tickets from Tito API
  - `build` - Generates the badge PDF from tickets and speakers JSON files
  - `blank-tickets` - Generates blank badges for last-minute attendees
- **`update-ticket-references.py`** - Updates ticket reference codes based on a JSON mapping file

### Alternative Usage

You can also run the scripts directly without using Task:

```bash
# Convert Sessionize data
python convert-sessionize-to-json.py pycon-ireland-2025-sessionize.xlsx pycon-ireland-2025-speakers.json

# Download tickets
python build_badge.py download-tickets --event pycon-ireland-2025 --store-name pycon-ireland-2025-tickets.json

# Generate badges
python build_badge.py build pycon-ireland-2025-tickets.json --speakers pycon-ireland-2025-speakers.json --output pycon-ireland-2025-badges.pdf

# Generate blank badges
python build_badge.py blank-tickets --limit 1

# Update ticket references
python update-ticket-references.py \
    pycon-ireland-2025-tickets.json \
    reference-mapping.json \
    pycon-ireland-2025-tickets-updated.json
```
