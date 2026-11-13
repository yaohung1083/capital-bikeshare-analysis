"""Read station activity from the imported Capital Bikeshare database."""

import os
import sqlite3
from contextlib import closing
from datetime import datetime
from pathlib import Path
from typing import Annotated

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel


app = FastAPI(title="Capital Bikeshare Station Activity")
DEFAULT_DB = Path(__file__).resolve().parent / "data" / "bikeshare.sqlite3"


class StationActivity(BaseModel):
    station_id: str
    start: datetime
    end: datetime
    departures: int
    arrivals: int
    net_departures: int


@app.get("/stations/{station_id}/activity", response_model=StationActivity)
def station_activity(
    station_id: str,
    start: Annotated[str, Query(description="ISO 8601 date and time without a timezone offset")],
    end: Annotated[str, Query(description="Exclusive ISO 8601 end time without a timezone offset")],
):
    try:
        # Require a date and a time, and preserve the precision stored by the importer.
        start_time, end_time = (datetime.fromisoformat(value) for value in (start, end))
        if any(len(value) <= 10 for value in (start, end)):
            raise ValueError
    except ValueError:
        raise HTTPException(422, "Use ISO 8601 date and time, e.g. 2025-01-14T08:00:00.") from None
    if start_time.tzinfo is not None or end_time.tzinfo is not None:
        raise HTTPException(422, "Use dataset timestamps without a timezone offset.")
    if start_time >= end_time:
        raise HTTPException(422, "start must be earlier than end.")

    start_key = start_time.isoformat(sep=" ", timespec="microseconds")
    end_key = end_time.isoformat(sep=" ", timespec="microseconds")
    database = Path(os.environ.get("BIKESHARE_DB", DEFAULT_DB)).resolve()
    try:
        with closing(sqlite3.connect(f"{database.as_uri()}?mode=ro", uri=True)) as db:
            departures, arrivals = db.execute("""
                SELECT
                    (SELECT COUNT(*) FROM trips
                     WHERE start_station_id = ? AND started_at >= ? AND started_at < ?),
                    (SELECT COUNT(*) FROM trips
                     WHERE end_station_id = ? AND ended_at >= ? AND ended_at < ?)
            """, (station_id, start_key, end_key, station_id, start_key, end_key)).fetchone()
    except sqlite3.Error as error:
        raise HTTPException(503, "Trip database is unavailable. Run import_trips.py first.") from error

    return StationActivity(
        station_id=station_id,
        start=start_time,
        end=end_time,
        departures=departures,
        arrivals=arrivals,
        net_departures=departures - arrivals,
    )
