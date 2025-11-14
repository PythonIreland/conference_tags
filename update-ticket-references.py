#!/usr/bin/env python
"""
Update ticket references based on a JSON mapping configuration file.

This script reads a tickets JSON file, applies reference transformations
based on a mapping file, and outputs a new tickets JSON file.

Example mapping file (reference-mapping.json):
{
    "BBGQ-1": "KARA-TE",
    "XYZA-2": "JUDO-42"
}
"""

import json
import sys
from pathlib import Path

import typer
from pydantic import TypeAdapter, ValidationError

from models import TicketModel

app = typer.Typer(help="Update ticket references based on a JSON mapping configuration")


def load_tickets(input_file: Path) -> list[TicketModel]:
    """Load and validate tickets from JSON file."""
    try:
        with open(input_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Validate using TypeAdapter for list of TicketModel
        adapter = TypeAdapter(list[TicketModel])
        tickets = adapter.validate_python(data)

        typer.echo(f"✓ Loaded {len(tickets)} tickets from {input_file}")
        return tickets

    except FileNotFoundError:
        typer.echo(f"✗ Error: Input file '{input_file}' not found", err=True)
        raise typer.Exit(code=1)
    except json.JSONDecodeError as e:
        typer.echo(f"✗ Error: Invalid JSON in '{input_file}': {e}", err=True)
        raise typer.Exit(code=1)
    except ValidationError as e:
        typer.echo(f"✗ Error: Validation failed for tickets: {e}", err=True)
        raise typer.Exit(code=1)


def load_mapping(mapping_file: Path) -> dict[str, str]:
    """Load reference mapping from JSON file."""
    try:
        with open(mapping_file, "r", encoding="utf-8") as f:
            mapping = json.load(f)

        if not isinstance(mapping, dict):
            typer.echo(
                f"✗ Error: Mapping file must contain a JSON object (dict), got {type(mapping).__name__}",
                err=True,
            )
            raise typer.Exit(code=1)

        # Validate that all keys and values are strings
        for key, value in mapping.items():
            if not isinstance(key, str) or not isinstance(value, str):
                typer.echo(
                    f"✗ Error: Mapping keys and values must be strings, got {key}: {value}",
                    err=True,
                )
                raise typer.Exit(code=1)

        typer.echo(f"✓ Loaded {len(mapping)} reference mappings from {mapping_file}")
        return mapping

    except FileNotFoundError:
        typer.echo(f"✗ Error: Mapping file '{mapping_file}' not found", err=True)
        raise typer.Exit(code=1)
    except json.JSONDecodeError as e:
        typer.echo(f"✗ Error: Invalid JSON in '{mapping_file}': {e}", err=True)
        raise typer.Exit(code=1)


def apply_reference_mapping(
    tickets: list[TicketModel], mapping: dict[str, str]
) -> tuple[list[TicketModel], int]:
    """
    Apply reference mapping to tickets.

    Returns:
        Tuple of (updated_tickets, count_of_changes)
    """
    updated_tickets = []
    changes_count = 0

    for ticket in tickets:
        if ticket.reference in mapping:
            old_ref = ticket.reference
            new_ref = mapping[old_ref]

            # Create a new ticket with updated reference
            # Use model_copy to create a modified copy
            updated_ticket = ticket.model_copy(update={"reference": new_ref})
            updated_tickets.append(updated_ticket)

            typer.echo(f"  {old_ref} → {new_ref}")
            changes_count += 1
        else:
            # Keep ticket as-is
            updated_tickets.append(ticket)

    return updated_tickets, changes_count


def save_tickets(tickets: list[TicketModel], output_file: Path) -> None:
    """Save tickets to JSON file."""
    try:
        # Convert pydantic models to dict for JSON serialization
        adapter = TypeAdapter(list[TicketModel])
        data = adapter.dump_python(tickets, mode="json")

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

        typer.echo(f"✓ Saved {len(tickets)} tickets to {output_file}")

    except Exception as e:
        typer.echo(f"✗ Error: Failed to save tickets: {e}", err=True)
        raise typer.Exit(code=1)


@app.command()
def update(
    input_file: Path = typer.Argument(
        ..., help="Input tickets JSON file (e.g., pycon-ireland-2025-tickets.json)"
    ),
    mapping_file: Path = typer.Argument(
        ..., help="JSON file containing reference mappings"
    ),
    output_file: Path = typer.Argument(
        ..., help="Output tickets JSON file with updated references"
    ),
    dry_run: bool = typer.Option(
        False, "--dry-run", "-n", help="Show what would be changed without writing"
    ),
) -> None:
    """
    Update ticket references based on a mapping file.

    The mapping file should be a JSON object where keys are old references
    and values are new references:

    \b
    {
        "BBGQ-1": "KARA-TE",
        "XYZA-2": "JUDO-42"
    }

    Example usage:

    \b
    # Update references
    python update-ticket-references.py \\
        pycon-ireland-2025-tickets.json \\
        reference-mapping.json \\
        pycon-ireland-2025-tickets-updated.json

    \b
    # Dry run to preview changes
    python update-ticket-references.py \\
        pycon-ireland-2025-tickets.json \\
        reference-mapping.json \\
        pycon-ireland-2025-tickets-updated.json \\
        --dry-run
    """
    typer.echo("🎫 Ticket Reference Updater")
    typer.echo("=" * 50)

    # Load tickets
    tickets = load_tickets(input_file)

    # Load mapping
    mapping = load_mapping(mapping_file)

    # Apply mapping
    typer.echo("\n📝 Applying reference mappings:")
    updated_tickets, changes_count = apply_reference_mapping(tickets, mapping)

    # Summary
    typer.echo("\n" + "=" * 50)
    typer.echo(f"Summary:")
    typer.echo(f"  Total tickets: {len(tickets)}")
    typer.echo(f"  References updated: {changes_count}")
    typer.echo(f"  Unchanged: {len(tickets) - changes_count}")

    # Save or dry-run
    if dry_run:
        typer.echo("\n⚠️  DRY RUN - No files were modified")
    else:
        typer.echo("")
        save_tickets(updated_tickets, output_file)
        typer.echo("\n✅ Update complete!")


if __name__ == "__main__":
    app()
