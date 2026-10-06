'Restore archived CSV files from the GitHub package; do not run simulations.'

import gzip
import hashlib
import json
import os
from pathlib import Path
import shutil
import tempfile


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main():
    results = Path(__file__).resolve().parents[1] / "results"
    manifest = results / "archives" / "manifest.json"
    if not manifest.exists():
        raise FileNotFoundError('Missing results/archives/manifest.json: use the prepared Kairos Labs package.')
    records = json.loads(manifest.read_text(encoding="utf-8"))["files"]
    restored = 0
    for record in records:
        name = record["name"]
        if Path(name).name != name or not name.endswith(".csv"):
            raise ValueError('Invalid filename in the manifest.')
        archive = results / "archives" / (name + ".gz")
        target = results / name
        if sha256(archive) != record["gzip_sha256"]:
            raise ValueError(f"Modified compressed archive: {archive.name}")
        if target.exists():
            if sha256(target) != record["csv_sha256"]:
                raise ValueError(f"Existing CSV differs; refusing overwrite: {name}")
            continue
        with tempfile.NamedTemporaryFile(dir=results, delete=False) as stream:
            temporary = Path(stream.name)
            try:
                with gzip.open(archive, "rb") as source:
                    shutil.copyfileobj(source, stream)
                stream.flush()
                if temporary.stat().st_size != record["csv_bytes"] or sha256(temporary) != record["csv_sha256"]:
                    raise ValueError(f"Inconsistent restored CSV: {name}")
                # Create the destination without replacing a file created during restoration.
                os.link(temporary, target)
                restored += 1
            finally:
                temporary.unlink(missing_ok=True)
    print(f"Restored CSV files: {restored}; verified archives: {len(records)}. No simulations.")


if __name__ == "__main__":
    main()
