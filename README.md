# conference_tags

Add tito API token in `.secret.toml`
TITO_TOKEN = "some_secret"
You can find your API key by signing in at https://api.tito.io.

All colors in the pdf construction must be CYMK defined as we target print.
colros are currently defined in build_badges

Add ttf fonts in `./fonts`

we use `UbuntuMono-R.ttf` because it makes a clear distinction between
0 and O, and 1 and l and I
The Bree font we use id not free, we bought a licence for it.
You'll find the ttf files in our google drive.

setup the script in `settings.toml`

run `build_badges.py`