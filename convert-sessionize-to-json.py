import json
import pathlib

import typer
from openpyxl.reader.excel import load_workbook

from models import SpeakerModel

app = typer.Typer()


@app.command()
def main(sessionize_file: pathlib.Path):
    wb = load_workbook(filename=sessionize_file)
    sheet = wb["Accepted speakers"]

    fields = SpeakerModel.__fields__.keys()

    speakers = [
        SpeakerModel(**dict(zip(fields, row)))
        for row in sheet.iter_rows(min_row=2, max_col=4, values_only=True)
    ]

    speakers.sort(key=lambda speaker: speaker.full_name)

    with open("speakers.json", "w") as fp:
        json.dump(
            fp=fp,
            obj=list(map(SpeakerModel.dict, speakers)),
            indent=4,
        )


if __name__ == "__main__":
    app()
