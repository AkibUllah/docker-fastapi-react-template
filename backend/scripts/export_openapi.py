"""Write the API's OpenAPI document to a file (default: openapi.json).

Used by the GitHub Pages workflow to publish a static API reference. ``create_app`` only
wires the application; the database and Redis are opened in the lifespan hook, not at
import time, so no .env or services are needed.

    python scripts/export_openapi.py [OUTPUT_PATH]
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.main import create_app  # noqa: E402


def main(argv: list[str]) -> int:
    out = Path(argv[1]) if len(argv) > 1 else Path("openapi.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    schema = create_app().openapi()
    out.write_text(json.dumps(schema, indent=2) + "\n")
    print(f"wrote {out} ({len(schema['paths'])} paths)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
