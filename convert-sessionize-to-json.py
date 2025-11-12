import json
import pathlib
import typing
import typer
from openpyxl.reader.excel import load_workbook
import pandas as pd

from models import SpeakerModel

app = typer.Typer()


@app.command()
def main(
    sessionize_file: typing.Annotated[
        pathlib.Path,
        typer.Argument(help="Sessionize file", default=...),
    ],
    speakers_file: typing.Annotated[
        pathlib.Path,
        typer.Argument(help="JSON target file for the accepted speakers", default=...),
    ],
):
    columns = {
        "Speaker Id": "speaker_id",
        "FirstName": "first_name",
        "LastName": "last_name",
        "Email": "email",
    }
    df: pd.DataFrame = pd.read_excel(
        sessionize_file,
        sheet_name="Accepted speakers",
        usecols=columns.keys(),
    ).rename(columns=columns)
    df['email'] = df['email'].str.lower()
    df['full_name'] = df['first_name'] + ' ' + df['last_name']
    df = df.sort_values(by=['full_name'],ascending=True)
    df.to_json(speakers_file, orient="records", indent=4)


if __name__ == "__main__":
    app()
