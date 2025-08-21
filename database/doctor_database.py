import json
import os
import sqlite3
from pathlib import Path
from typing import List, Dict, Optional, Iterable, Any

from database.patient_database import BookingManager


class DoctorDB:
    def __init__(self, db_name: str = "my_database.db", folder_name: str = "db"):
        # Get the absolute path to the folder where *this script* lives
        base_dir = os.path.dirname(os.path.abspath(__file__))
        # Define a folder (e.g., "db") inside that directory
        db_folder = os.path.join(base_dir, folder_name)
        # Create the folder if it doesn't exist
        os.makedirs(db_folder, exist_ok=True)
        # Full path to the database file
        self.db_path = os.path.join(db_folder, db_name)
        # Connect to the database
        self._conn = sqlite3.connect(self.db_path)
        self._conn.row_factory = sqlite3.Row
        # Initialize the table(s)
        self._ensure_table()
    # ---------- Schema ----------
    def _ensure_table(self) -> None:
        cur = self._conn.cursor()
        cur.execute("""
        CREATE TABLE IF NOT EXISTS doctors (
            doctor_name TEXT NOT NULL UNIQUE,
            expertise   TEXT NOT NULL,
            timings     TEXT NOT NULL,
            max_slots   INTEGER NOT NULL,
            slots_remaining INTEGER NOT NULL
        )
        """)
        self._conn.commit()

    # ---------- Ingest / Upsert ----------
    def upsert_many(self, doctors: Iterable[Dict[str, Any]]) -> None:
        """
        Upsert list of dicts with keys:
        doctor_name, expertise, timings, max_slots, slots_remaining
        """
        cur = self._conn.cursor()
        cur.executemany("""
        INSERT INTO doctors (doctor_name, expertise, timings, max_slots, slots_remaining)
        VALUES (:doctor_name, :expertise, :timings, :max_slots, :slots_remaining)
        ON CONFLICT(doctor_name) DO UPDATE SET
            expertise=excluded.expertise,
            timings=excluded.timings,
            max_slots=excluded.max_slots,
            slots_remaining=excluded.slots_remaining
        """, doctors)
        self._conn.commit()

    def load_from_json_file(self, json_path: str) -> None:
        data = json.loads(Path(json_path).read_text(encoding="utf-8"))
        if not isinstance(data, list):
            raise ValueError("JSON root must be a list of doctor objects.")
        self.upsert_many(data)

    # ---------- Queries ----------
    def get_all(self) -> List[Dict[str, Any]]:
        cur = self._conn.cursor()
        rows = cur.execute("""
            SELECT doctor_name, expertise, timings, max_slots, slots_remaining
            FROM doctors
            ORDER BY doctor_name
        """).fetchall()
        return [dict(row) for row in rows]

    def get_by_name(self, doctor_name: str) -> Optional[Dict[str, Any]]:
        cur = self._conn.cursor()
        row = cur.execute("""
            SELECT doctor_name, expertise, timings, max_slots, slots_remaining
            FROM doctors WHERE doctor_name = ?
        """, (doctor_name,)).fetchone()
        return dict(row) if row else None

    # ---------- Booking / Slot updates ----------
    def book_slot(self, doctor_name: str, slots: int = 1) -> bool:
        """
        Decrement slots_remaining by `slots` if available.
        Returns True if booked, False if not enough slots or doctor not found.
        """
        cur = self._conn.cursor()
        row = cur.execute("""
            SELECT slots_remaining FROM doctors WHERE doctor_name = ?
        """, (doctor_name,)).fetchone()

        if not row:
            return False

        remaining = int(row["slots_remaining"])
        if remaining < slots:
            print('error booking slot')
            return False

        cur.execute("""
            UPDATE doctors
            SET slots_remaining = slots_remaining - ?
            WHERE doctor_name = ?
        """, (slots, doctor_name))
        self._conn.commit()
        return True

    def cancel_slot(self, doctor_name: str, slots: int = 1) -> bool:
        """
        Increment slots_remaining by `slots` but never exceed max_slots.
        Returns True if successful, False if doctor not found.
        """
        cur = self._conn.cursor()
        row = cur.execute("""
            SELECT max_slots, slots_remaining FROM doctors WHERE doctor_name = ?
        """, (doctor_name,)).fetchone()
        if not row:
            return False

        max_slots = int(row["max_slots"])
        remaining = int(row["slots_remaining"])
        new_val = min(max_slots, remaining + slots)

        cur.execute("""
            UPDATE doctors SET slots_remaining = ? WHERE doctor_name = ?
        """, (new_val, doctor_name))
        self._conn.commit()
        return True

    # ---------- JSON export (feed to LLM) ----------
    def to_json(self, pretty: bool = True) -> str:
        data = self.get_all()
        return json.dumps(data, indent=2 if pretty else None)

    def export_json_file(self, out_path: str, pretty: bool = True) -> None:
        Path(out_path).write_text(self.to_json(pretty=pretty), encoding="utf-8")

    # ---------- Cleanup ----------
    def close(self) -> None:
        if self._conn:
            self._conn.close()
            self._conn = None


# -------------------------
# Example usage
# -------------------------
if __name__ == "__main__":
    db = DoctorDB()
    bm = BookingManager()
    print(bm.list_bookings_for_day())
    db.close()
