# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a conference badge generation system for PyCon Ireland that creates print-ready, CMYK-safe PDF badges by combining:
- **Tito** ticket data (attendee information via API)
- **Sessionize** speaker data (from exported Excel files)

The output is a professional PDF suitable for printing on A4/A5 paper with proper color profiles for commercial printing.

## Key Commands

All commands use Task (taskfile.dev). Run `task --list` to see all available tasks.

### Complete Workflow
```bash
task workflow:complete  # Automated: convert → download → generate
```

### Individual Steps
```bash
task sessionize:convert      # Convert Excel → JSON (requires pycon-ireland-YYYY-sessionize.xlsx)
task tito:download:tickets   # Download tickets from Tito API
task badges:generate         # Generate PDF from tickets + speakers JSON
task badges:blank            # Generate blank badges for last-minute attendees
task report:generate         # Create Excel report comparing tickets and speakers
```

### Environment Management
```bash
task environment:create   # Create venv
task environment:install  # Install dependencies
task environment:reset    # Full reset (drop + create + install)
```

### Code Quality
```bash
task format:ruff          # Format all Python files
task format:ruff -- file.py   # Format specific file
```

### Utilities
```bash
task check           # Verify setup (fonts, config, tools)
task show:files      # List generated files for current year
task clean           # Remove generated files for current year
```

## Configuration System

Configuration is managed via **Dynaconf** (config.py:1-6) which loads settings from:
1. `settings.toml` - Project settings (API account, event name, fonts, paper size, etc.)
2. `.secret.toml` - API tokens (gitignored)

### Critical Settings
- `settings.API.account` - Tito account name (default: "python-ireland")
- `settings.API.event` - Event slug (e.g., "pycon-ireland-2025")
- `settings.TITO_TOKEN` - Tito API token (stored in .secret.toml)
- `settings.fonts.*` - Font file names (must exist in ./fonts/)
- `settings.printout.paper_size` - "A4" or "A5"
- `settings.printout.debug` - Boolean for debug mode

The Taskfile.yaml uses a YEAR variable (default: 2025) to construct file names like `pycon-ireland-2025-tickets.json`.

## Data Flow Architecture

### 1. Speaker Data (Sessionize → JSON)
**Script**: `convert-sessionize-to-json.py`
- **Input**: `pycon-ireland-YYYY-sessionize.xlsx` (downloaded from Sessionize export)
  - Direct URL: https://sessionize.com/app/organizer/export/excel/19814/Accepted_sessions
  - Contains "Accepted speakers" sheet with Speaker Id, FirstName, LastName, Email
- **Process**:
  - Reads "Accepted speakers" sheet using pandas/openpyxl
  - Normalizes emails to lowercase
  - Validates against SpeakerModel (pydantic)
- **Output**: `pycon-ireland-YYYY-speakers.json` with structure:
  ```json
  [{"speaker_id": "...", "first_name": "...", "last_name": "...", "email": "..."}]
  ```

### 2. Ticket Data (Tito API → JSON)
**Script**: `build_badge.py download-tickets` (uses `get_tickets.py`)
- **API**: Tito v3 REST API with pagination
- **Process**:
  - Fetches from `https://api.tito.io/v3/{account}/{event}/tickets?page={N}&view=extended`
  - Uses bearer token auth from settings
  - Paginates through all tickets using `meta.next_page`
  - Validates against TicketModel (pydantic)
- **Output**: `pycon-ireland-YYYY-tickets.json` with structure:
  ```json
  [{"first_name": "...", "last_name": "...", "email": "...", "reference": "...",
    "release_title": "...", "responses": {...}, "created_at": "...", "speaker": false, "exhibitor": false}]
  ```

### 3. Email Mapping (Optional)
**File**: `emails.mapping.csv` (gitignored)
- **Purpose**: Maps mismatched emails between Sessionize and Tito
- **Format**: CSV with columns `tito_email,sessionize_email`
- **Usage**: Automatically loaded by `build_badge.py` and `merge_sessionize_tito_emails.py` if exists
- **When needed**: Speaker uses different email on Sessionize vs. Tito purchase

### 4. Badge Generation (JSON → PDF)
**Script**: `build_badge.py build`
- **Inputs**: tickets JSON + speakers JSON + (optional) emails.mapping.csv
- **Process**:
  1. Loads tickets and marks speakers based on email matching (with mapping support)
  2. Registers fonts from ./fonts/ directory (build_badge.py:36-57)
  3. Creates LayoutParameters based on paper size from settings (build_badge.py:65-142)
  4. Uses ReportLab to draw badges with:
     - CMYK colors (irish_green, irish_orange, banner_blue defined at build_badge.py:60-62)
     - QR codes with ticket reference
     - Font hierarchy: conference font (headers), name font (names), reference font (codes)
  5. Handles two-per-page layout for A5 or single-per-page for other sizes
- **Output**: `pycon-ireland-YYYY-badges.pdf` (CMYK print-ready)

### 5. Report Generation (Comparison)
**Script**: `merge_sessionize_tito_emails.py`
- **Purpose**: Identify speakers without tickets
- **Process**:
  - Joins tickets and speakers DataFrames on email (with mapping support)
  - Generates 4 sheets: All Tickets, All Speakers, Missing Speakers, Speakers with Ticket
- **Output**: `pycon-ireland-YYYY-report.xlsx`

## Data Models (models.py)

### TicketModel
- Represents a Tito ticket/attendee
- Key properties:
  - `display_name`: Formatted as "FirstName L." for badges
  - `level`: Python experience level from responses dict
  - `speaker`: Boolean flag set during badge generation
  - `exhibitor`: Boolean flag

### SpeakerModel
- Represents a Sessionize speaker
- Fields: speaker_id, first_name, last_name, email
- Property `full_name`: Combined first + last name

### TicketAPIModel
- Wrapper for paginated Tito API responses
- Contains list of tickets + pagination metadata

## Font Requirements

Required fonts in `./fonts/` directory:
- **UbuntuMono-R.ttf** - Reference font (clearly distinguishes 0/O, 1/l/I)
- **Bree fonts** (BreeBold.ttf, BreeSerif-Regular.ttf) - Licensed, stored in Google Drive

Font registration happens in `build_badge.py:register_fonts()` before PDF generation.

## Color System

All colors are CMYK for professional printing (build_badge.py:60-62):
- `irish_green = PCMYKColor(71, 0, 72, 40)`
- `irish_orange = PCMYKColor(0, 43, 91, 0)`
- `banner_blue = PCMYKColor(98, 82, 0, 44)`

Never use RGB colors in badge generation code.

## Dependencies

Currently using `requirements.txt` but transitioning to `pyproject.toml` + `uv`:
- **dynaconf** - Configuration management
- **marshmallow** - Data serialization (legacy, being replaced by pydantic)
- **openpyxl** - Excel file reading
- **pydantic** - Data validation and models
- **reportlab** - PDF generation
- **requests** - Tito API calls
- **typer** - CLI framework
- **pandas** - Data processing

External tools (optional but recommended):
- **jq** - JSON processing for ticket counting
- **httpie** - Alternative API testing

## Important Notes

### Task Preconditions
Many tasks have preconditions that check for required files. If a task fails with a precondition error, the error message indicates which command to run first (e.g., "Run 'task tito:download:tickets' first").

### Smart Rebuilds
Task tracks file dependencies (sources/generates). If source files haven't changed, dependent tasks skip execution automatically.

### Year Management
The YEAR variable in Taskfile.yaml controls which event files are processed. Update it when preparing for a new conference year.

### Debug Mode
When `settings.printout.debug = true`, output files use simple names (e.g., "tickets.pdf" instead of timestamped names).

### Speaker Identification
Speakers are identified by matching their Sessionize email against Tito ticket emails. The `emails.mapping.csv` file solves mismatches. The badge generation code sets `ticket.speaker = True` for matched emails.
