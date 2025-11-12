# Changelog

## 2025-11-12 - Major Taskfile and Documentation Improvements

### Breaking Changes
- Removed duplicate task `tito:download:current` (use `tito:download:tickets` instead)
- Standardized all file naming to `pycon-ireland-YYYY-{type}.{ext}` format

### New Features

#### Workflow Automation
- **`task workflow:complete`** - Complete automated workflow (convert → download → generate)
- Runs all steps with a single command when Sessionize file is ready

#### Validation & Checks
- **`task check`** - Verify environment setup (tokens, venv, fonts, tools)
- All critical tasks now have precondition checks with helpful error messages
- Smart file dependency tracking with `sources:` and `generates:`

#### Utilities
- **`task show:files`** - List all generated files for current event
- **`task show`** - Display current YEAR and EVENT variables
- **`task clean`** - Remove generated files for current event
- **`task clean:all`** - Remove all generated files (with confirmation prompt)

#### Documentation
- Added `summary:` blocks to all major tasks
- Use `task --summary <task-name>` for detailed task information
- Precondition messages guide users on which command to run next

### Improvements

#### File Naming Consistency
- **Tickets:** `pycon-ireland-YYYY-tickets.json`
- **Speakers:** `pycon-ireland-YYYY-speakers.json`  
- **Badges:** `pycon-ireland-YYYY-badges.pdf`
- **Reports:** `pycon-ireland-YYYY-report.xlsx`

#### Task Names
- `app:sessionize:speakers` → `sessionize:convert`
- `download:current` → `tito:download:tickets`
- `app:tickets:download` → removed (duplicate)
- `download:tickets:all` → `tito:download:all`
- `app:badges` → `badges:generate`
- `app:count-tickets` → `tickets:count`
- `tickets-count` → `tito:count:api`
- `app:tickets:graph` → `tickets:graph`
- `merge:tickets` → `report:generate`
- `distribution:size:*` → `tshirts:distribution:*`

#### Task Descriptions
- All descriptions now show exact file names using `{{ .EVENT }}` interpolation
- Example: "Download tickets for pycon-ireland-2025 → pycon-ireland-2025-tickets.json"
- Clearer, more informative output in `task --list`

#### Code Quality
- Created `PYTHON` variable for consistent virtualenv usage
- All Python commands now use `{{ .PYTHON }}`
- Uniform virtualenv usage across all tasks
- Removed hardcoded Tito token (was in `tito:count:api`)

#### Badge Generation
- Added `--output` parameter to `build_badge.py` command
- Automatic deletion of old PDF before generation
- Predictable output filename: `pycon-ireland-YYYY-badges.pdf`

### Documentation Updates

#### README.md
- Added "Quick Start - Automated Workflow" section
- New "Useful Tips" section covering:
  - Checking setup with `task check`
  - Viewing files with `task show:files`
  - Getting task details with `task --summary`
  - Cleaning up with `task clean`
  - **Email mapping for speakers** - Complete documentation with examples
- Updated "Available Tasks" with all new commands
- Added notes about smart rebuilds and error handling
- Reorganized for better flow and discoverability

#### Taskfile.yaml
- 10+ new tasks added
- All tasks have descriptive `desc:` fields
- Major tasks include detailed `summary:` documentation
- Preconditions prevent common errors
- Smart dependencies with `sources:` and `generates:`

### Technical Improvements

#### Error Prevention
- File existence checks before operations
- Tool availability checks (jq, httpie)
- Virtual environment validation
- Clear error messages with actionable guidance

#### Performance
- Task caching based on file timestamps
- Only rebuilds when source files change
- Faster iteration during development

#### Developer Experience  
- One-command workflow for common tasks
- Self-documenting task summaries
- Consistent naming conventions
- Helpful error messages
- Easy cleanup and reset options

### Migration Guide

If you have scripts using old task names:

```bash
# Old → New
task download:current          → task tito:download:tickets
task app:sessionize:speakers   → task sessionize:convert
task app:badges                → task badges:generate
task app:count-tickets         → task tickets:count
task app:tickets:graph         → task tickets:graph
task merge:tickets             → task report:generate
task distribution:size:current → task tshirts:distribution:current
```

### Files Changed
- `Taskfile.yaml` - Complete overhaul with 10+ improvements
- `README.md` - Comprehensive documentation update
- `build_badge.py` - Added `--output` parameter to `build` command
- `.gitignore` - Added specific patterns for generated files
- `emails.mapping.csv.example` - Added template for email mappings

### Statistics
- **10 major improvements** implemented
- **13 task names** standardized
- **6 new utility tasks** added
- **20+ tasks** now have precondition checks
- **15+ tasks** have detailed summaries
