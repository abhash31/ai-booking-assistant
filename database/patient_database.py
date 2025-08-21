import os
import sqlite3
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import uuid
import re


def _parse_timings(timings: str) -> tuple[datetime, datetime]:
    """
    Parse '9:00 AM - 12:00 PM' -> (start_dt, end_dt) using today's date.
    Only time-of-day matters.
    """
    # Normalize spaces
    timings = re.sub(r"\s+", " ", timings.strip())
    start_s, end_s = [s.strip() for s in timings.split("-")]
    today = datetime.now().date()
    start_dt = datetime.strptime(f"{today} {start_s}", "%Y-%m-%d %I:%M %p")
    end_dt = datetime.strptime(f"{today} {end_s}", "%Y-%m-%d %I:%M %p")
    return start_dt, end_dt


def _short_ref() -> str:
    return uuid.uuid4().hex[:8].upper()


class BookingManager:
    def __init__(self, db_name: str = "my_database.db", folder_name: str = "db"):
        # Get absolute path to the folder where this script lives
        base_dir = os.path.dirname(os.path.abspath(__file__))

        # Create full path to the desired database folder
        db_folder = os.path.join(base_dir, folder_name)
        os.makedirs(db_folder, exist_ok=True)  # Ensure the folder exists

        # Full path to the database file
        self.db_path = os.path.join(db_folder, db_name)

        # Connect to the database
        self._conn = sqlite3.connect(self.db_path)
        self._conn.row_factory = sqlite3.Row

        # Create necessary tables
        self._ensure_tables()

    def _ensure_tables(self):
        cur = self._conn.cursor()
        # doctors table assumed created by DoctorDB
        cur.execute("""
        CREATE TABLE IF NOT EXISTS bookings (
            patient_name TEXT NOT NULL,
            patient_age INTEGER NOT NULL,
            doctor_name TEXT NOT NULL,
            expertise TEXT,
            date TEXT NOT NULL,    -- YYYY-MM-DD
            time TEXT NOT NULL     -- HH:MM (24h)
        )
        """)
        # cur.execute("""
        # CREATE UNIQUE INDEX IF NOT EXISTS idx_unique_slot
        # ON bookings(doctor_name, date, time)
        # """)
        self._conn.commit()

    # ---------- Helpers ----------
    def _get_doctor(self, doctor_name: str) -> Optional[Dict[str, Any]]:
        cur = self._conn.cursor()
        row = cur.execute("""
            SELECT doctor_name, expertise, timings, max_slots, slots_remaining
            FROM doctors WHERE doctor_name = ?
        """, (doctor_name,)).fetchone()
        return dict(row) if row else None

    def _get_existing_times(self, doctor_name: str, date_str: str) -> set[str]:
        cur = self._conn.cursor()
        rows = cur.execute("""
            SELECT time FROM bookings
            WHERE doctor_name = ? AND date = ?
            ORDER BY time
        """, (doctor_name, date_str)).fetchall()
        return {r["time"] for r in rows}

    def _compute_all_slots(self, timings: str, max_slots: int) -> List[str]:
        """
        Split the doctor's window into equal blocks count = max_slots.
        Return list of 'HH:MM' (24h).
        """
        start_dt, end_dt = _parse_timings(timings)
        total_minutes = int((end_dt - start_dt).total_seconds() // 60)
        if max_slots <= 0 or total_minutes <= 0:
            return []
        slot_len = total_minutes // max_slots
        slot_len = max(slot_len, 1)
        slots = []
        t = start_dt
        for _ in range(max_slots):
            slots.append(t.strftime("%H:%M"))
            t += timedelta(minutes=slot_len)
            if t > end_dt:
                break
        return slots

    # ---------- Availability ----------
    def list_available_slots(self, doctor_name: str, date_str: str) -> List[str]:
        doctor = self._get_doctor(doctor_name)
        if not doctor:
            return []
        all_slots = self._compute_all_slots(doctor["timings"], int(doctor["max_slots"]))
        taken = self._get_existing_times(doctor_name, date_str)
        return [s for s in all_slots if s not in taken]

    # ---------- Booking ----------
    def book_earliest(
        self,
        patient_name: str,
        patient_age: int,
        doctor_name: str,
        date_str: str,
            time: str,
        # date_str: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Books the earliest available slot for doctor on date_str (default: today).
        Returns booking dict with ref if successful; None otherwise.
        Also decrements doctors.slots_remaining (floor=0).
        """
        doctor = self._get_doctor(doctor_name)
        # if not doctor:
        #     print(doctor, "name is wrong")
        #     return None

        # # Check remaining capacity
        # if int(doctor["slots_remaining"]) <= 0:
        #     print("no slots")
        #     return None

        # available = self.list_available_slots(doctor_name, date_of_app)
        # if not available:
        #     return None
        #
        # earliest = available[0]

        # Insert booking
        ref = _short_ref()
        try:
            cur = self._conn.cursor()
            cur.execute("""
                INSERT INTO bookings (patient_name, patient_age, doctor_name, expertise, date, time)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (patient_name, int(patient_age), doctor_name, doctor["expertise"], date_str, time))

            # Decrement doctor's slots_remaining safely
            cur.execute("""
                UPDATE doctors
                SET slots_remaining = CASE
                    WHEN slots_remaining > 0 THEN slots_remaining - 1
                    ELSE 0
                END
                WHERE doctor_name = ?
            """, (doctor_name,))
            self._conn.commit()
            print("@@@@BOOKING DONE")
        except Exception as e:
            print("some error ", e)
            # Unique slot conflict (rare race condition); retry logic could go here.
            return None

        return {
            "patient": patient_name,
            "age": int(patient_age),
            "doctor": doctor_name,
            "expertise": doctor["expertise"],
            "date": date_str,
            "time": time
        }

    # ---------- Cancel ----------
    def cancel_by_ref(self, ref: str) -> bool:
        """
        Cancels a booking by reference and reclaims the slot (increments slots_remaining up to max_slots).
        """
        cur = self._conn.cursor()
        row = cur.execute("""
            SELECT doctor_name, date, time FROM bookings WHERE ref = ?
        """, (ref,)).fetchone()
        if not row:
            return False

        doctor_name = row["doctor_name"]
        # Delete booking
        cur.execute("DELETE FROM bookings WHERE ref = ?", (ref,))
        # Increment doctor's slots_remaining but not above max_slots
        cur.execute("""
            UPDATE doctors
            SET slots_remaining = MIN(max_slots, slots_remaining + 1)
            WHERE doctor_name = ?
        """, (doctor_name,))
        self._conn.commit()
        return True

    # ---------- Queries ----------
    def list_bookings_for_day(self, date_str: Optional[str] = None) -> List[Dict[str, Any]]:
        date_str = date_str or datetime.now().strftime("%Y-%m-%d")
        cur = self._conn.cursor()
        rows = cur.execute("""
            SELECT patient_name, patient_age, doctor_name, expertise, date, time
            FROM bookings
            WHERE date = ?
            ORDER BY doctor_name, time
        """, (date_str,)).fetchall()
        return [dict(r) for r in rows]

    def get_everything(self):
        cur = self._conn.cursor()
        rows = cur.execute("""
                    SELECT * FROM bookings
                """)
        return [dict(r) for r in rows]

    def get_booking(self, ref: str) -> Optional[Dict[str, Any]]:
        cur = self._conn.cursor()
        row = cur.execute("""
            SELECT patient_name, patient_age, doctor_name, expertise, date, time
            FROM bookings WHERE ref = ?
        """, (ref,)).fetchone()
        return dict(row) if row else None

    def close(self):
        if self._conn:
            self._conn.close()
            self._conn = None
