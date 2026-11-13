"""Import Capital Bikeshare trip ZIP files into SQLite."""

import argparse
import csv
import io
import sqlite3
from contextlib import closing
from datetime import datetime
from pathlib import Path
from zipfile import ZipFile


COLUMNS = (
    "ride_id", "started_at", "ended_at", "start_station_id",
    "end_station_id", "rideable_type", "member_casual",
)


def read_trips(archive_path):
    with ZipFile(archive_path) as archive:
        members = [
            name for name in archive.namelist()
            if name.lower().endswith(".csv") and "__MACOSX" not in Path(name).parts
        ]
        if len(members) != 1:
            raise ValueError(f"{archive_path}: expected exactly one trip CSV")
        with archive.open(members[0]) as member:
            reader = csv.DictReader(io.TextIOWrapper(member, encoding="utf-8-sig", newline=""))
            missing = set(COLUMNS).difference(reader.fieldnames or [])
            if missing:
                raise ValueError(f"{archive_path}: missing columns {', '.join(sorted(missing))}")

            for row in reader:
                if any(row[column] is None for column in COLUMNS):
                    raise ValueError(f"{archive_path}:{reader.line_num}: incomplete row")
                ride_id = row["ride_id"].strip()
                if not ride_id:
                    raise ValueError(f"{archive_path}:{reader.line_num}: empty ride_id")
                started, ended = (
                    datetime.fromisoformat(row[column])
                    for column in ("started_at", "ended_at")
                )
                if started.tzinfo is not None or ended.tzinfo is not None:
                    raise ValueError(f"{archive_path}:{reader.line_num}: expected timestamps without offsets")
                yield (
                    ride_id,
                    started.isoformat(sep=" ", timespec="microseconds"),
                    ended.isoformat(sep=" ", timespec="microseconds"),
                    *(row[column].strip() or None for column in COLUMNS[3:]),
                )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archives", nargs="+", type=Path)
    parser.add_argument("--db", required=True, type=Path)
    args = parser.parse_args()

    with closing(sqlite3.connect(args.db)) as db:
        with db:
            db.execute("BEGIN IMMEDIATE")
            db.execute("""
                CREATE TABLE IF NOT EXISTS trips (
                    ride_id TEXT PRIMARY KEY NOT NULL,
                    started_at TEXT NOT NULL,
                    ended_at TEXT NOT NULL,
                    start_station_id TEXT,
                    end_station_id TEXT,
                    rideable_type TEXT,
                    member_casual TEXT
                )
            """)
            for archive in args.archives:
                db.executemany("""
                    INSERT INTO trips (
                        ride_id, started_at, ended_at, start_station_id,
                        end_station_id, rideable_type, member_casual
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(ride_id) DO NOTHING
                """, read_trips(archive))
            db.execute("CREATE INDEX IF NOT EXISTS trips_start ON trips(start_station_id, started_at)")
            db.execute("CREATE INDEX IF NOT EXISTS trips_end ON trips(end_station_id, ended_at)")
            inserted = db.total_changes
            total = db.execute("SELECT COUNT(*) FROM trips").fetchone()[0]
    print(f"Inserted {inserted:,} trips. Total: {total:,}.")


if __name__ == "__main__":
    main()
