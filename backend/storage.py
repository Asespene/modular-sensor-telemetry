from contextlib import closing
from pathlib import Path
import sqlite3


DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent / "telemetry.db"

#initialize or create a db file at the specific path
def init_db(db_path: Path | str = DEFAULT_DB_PATH) -> None:
    #makes sure the parent dir exists before SQLITE creates or opens a db file
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    #opens or creates the database file at the path on disk,
    #returns a connecttion object we use to work with our db.
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS telemetry_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                schema_version INTEGER NOT NULL,
                sequence INTEGER NOT NULL,
                uptime_ms INTEGER NOT NULL,
                device_id TEXT NOT NULL,
                sensor_id TEXT NOT NULL,
                sensor_type TEXT NOT NULL,
                metric TEXT NOT NULL,
                unit TEXT NOT NULL,
                quality TEXT NOT NULL,
                received_at TEXT NOT NULL,
                value NUMERIC
            )
            """
        )
        conn.commit()
    finally:
        conn.close()

#parses the record data and then insert it into our db
def insert_telemetry(record: dict, db_path: str | Path = DEFAULT_DB_PATH) -> int:
    conn = sqlite3.connect(db_path)

    try:
        cursor = conn.execute(
            """
            INSERT INTO telemetry_records (
                schema_version, sequence, uptime_ms, device_id, sensor_id, sensor_type, metric, unit, quality, received_at, value
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (record['schema_version'], record['sequence'], record['uptime_ms'], record['device_id'], record['sensor_id'], record['sensor_type'], record['metric'], record['unit'], record['quality'], record['received_at'], record['value'])
        )
        conn.commit()
        #returns the index of the row we just inserted
        return cursor.lastrowid
    finally:
        conn.close()


#grab the newest record in the db from the telemetry table that matches the specific device and sensor id and return it as a line of dict
def get_latest_record(device_id: str, sensor_id: str, db_path: str | Path = DEFAULT_DB_PATH) -> dict | None:
    conn = sqlite3.connect(db_path)

    try:
        #configuration on how sqlite should return each row using the fetchone function
        conn.row_factory = sqlite3.Row
        #we are retreiving the query result set and assigning it to cursor so it acts as pointer to the result of the query
        cursor = conn.execute(
            """
                SELECT schema_version, sequence, uptime_ms, device_id, sensor_id, sensor_type, metric, unit, quality, received_at, value FROM telemetry_records 
                WHERE device_id = ? AND sensor_id = ?
                ORDER BY id DESC
                LIMIT 1
            """,
            (device_id, sensor_id)
        )
        #using said pointer we are dereferencing the value or grabbing the actual value of the query result in this case the entire row and columns that matches the where condition
        row = cursor.fetchone()

        #ensure we are returning a valid row, if it exists return it as is a dict type otherwise dont return anything
        return dict(row) if row is not None else None

    finally:
        conn.close()