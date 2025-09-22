# firebase_realtime_database.py
import firebase_admin
from firebase_admin import credentials, db

class FirebaseListener:
    def __init__(self, cred_path, db_url, ref_path):
        if not firebase_admin._apps:
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred, {'databaseURL': db_url})
        self.ref = db.reference(ref_path)
        self._stream = None

    def get_state(self):
        """Fetch the current value once (blocking)."""
        return self.ref.get()

    def start_listening(self, on_change):
        """Start streaming updates; on_change(new_value) is called per update."""
        def _listener(event):
            # event.event_type: 'put' | 'patch'
            # event.path: path from the ref you listened to
            # event.data: new value at that path
            new_val = event.data
            # If you point to a parent path, you may get a dict; narrow here if needed.
            # For your ref_path = 'CallState/state', event.data should be a scalar string.
            if on_change is not None:
                on_change(new_val)

        self._stream = self.ref.listen(_listener)
        return self._stream  # keep a handle if you want to close it later

    def stop(self):
        try:
            if self._stream:
                self._stream.close()
        except Exception:
            pass
