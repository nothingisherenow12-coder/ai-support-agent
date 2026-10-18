"""Restore a PostgreSQL custom-format backup, with an explicit destructive confirmation."""
import argparse
from pathlib import Path
import subprocess
import sys

REPO_ROOT = Path(__file__).resolve().parents[2]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("backup", type=Path, help="Path to a .dump file created by backup_database.py")
    args = parser.parse_args()
    backup = args.backup.resolve()
    if not backup.is_file():
        parser.error(f"Backup file does not exist: {backup}")
    print("WARNING: this replaces database objects and data in the current ai_support database.")
    if input("Type RESTORE to continue: ").strip() != "RESTORE":
        print("Restore cancelled.")
        return 2
    command = [
        "docker", "compose", "exec", "-T", "db", "pg_restore", "--clean", "--if-exists",
        "--no-owner", "--no-privileges", "-U", "postgres", "-d", "ai_support",
    ]
    try:
        with backup.open("rb") as stream:
            result = subprocess.run(command, cwd=REPO_ROOT, stdin=stream, check=False)
    except OSError as exc:
        print(f"Restore could not start: {exc}", file=sys.stderr)
        return 1
    if result.returncode:
        print("Restore failed. Inspect the database logs and verify the backup file.", file=sys.stderr)
        return result.returncode
    print("Restore completed. Verify the app and record counts before resuming service.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
