"""Create a binary-safe PostgreSQL backup from the Compose database service."""
from datetime import datetime, timezone
from pathlib import Path
import subprocess
import sys

REPO_ROOT = Path(__file__).resolve().parents[2]


def main() -> int:
    output_dir = REPO_ROOT / "backups"
    output_dir.mkdir(exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output = output_dir / f"ai-support-{timestamp}.dump"
    command = ["docker", "compose", "exec", "-T", "db", "pg_dump", "-U", "postgres", "-d", "ai_support", "-Fc"]
    try:
        with output.open("wb") as stream:
            result = subprocess.run(command, cwd=REPO_ROOT, stdout=stream, check=False)
        if result.returncode:
            output.unlink(missing_ok=True)
            print("Backup failed. Confirm Docker Compose is running and inspect the database logs.", file=sys.stderr)
            return result.returncode
    except OSError as exc:
        output.unlink(missing_ok=True)
        print(f"Backup could not start: {exc}", file=sys.stderr)
        return 1
    print(f"Backup created: {output}")
    print("Store this file securely outside the repository; it may contain customer data.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
