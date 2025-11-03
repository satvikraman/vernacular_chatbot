import logging
import os
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List

# --- GUARANTEED IMPORTS ---
# We assume these imports will not fail, even locally, 
# because the module is installed in the virtual environment.
from google.cloud import firestore
from google.cloud.firestore import Client, DocumentReference, DocumentSnapshot, ArrayUnion, Increment, SERVER_TIMESTAMP

# --- ENVIRONMENT CHECK (Placeholder) ---
# Replace with your actual import path: from app.utils.env import is_local
def is_local():
    """Mocks your environment check."""
    return os.environ.get("ENV") == "local"

# --- LOCAL MOCK DB ---
# Mocks the top-level collections as Python dictionaries
_local_db: Dict[str, Any] = {
    "public_stats": {}, # Stores 'overall_summary' and 'week_YYYYMMDD' documents
    "logs": {},         # Stores custom-named log documents
}

# -----------------------------
# 🔧 LOCAL MOCK DB IMPLEMENTATION
# -----------------------------
class LocalDocSnapshot:
    """Mock for a Firestore DocumentSnapshot."""
    def __init__(self, data: Dict):
        # Handle the SERVER_TIMESTAMP field mock when reading
        if data.get("date") == SERVER_TIMESTAMP:
            data["date"] = datetime.now()
        self._data = data

    def to_dict(self) -> Dict:
        """Returns the document data."""
        return self._data

    @property
    def exists(self) -> bool:
        """Mock for snapshot.exists."""
        return bool(self._data) and self._data != {}

class LocalDoc:
    """Mock for a Firestore DocumentReference."""
    def __init__(self, doc_id: str, parent_data: Dict):
        self.id = doc_id
        self._parent_data = parent_data
        # Initialize an empty dict if the document ID doesn't exist yet
        self._data = self._parent_data.setdefault(doc_id, {})

    def get(self) -> LocalDocSnapshot:
        """Mimics doc_ref.get()."""
        return LocalDocSnapshot(self._data)

    def set(self, new_data: Dict, merge: bool = False):
        """
        Mimics doc_ref.set(data, merge=...). 
        Critically, it handles Firestore's native Increment/ArrayUnion/SERVER_TIMESTAMP objects.
        """
        current_data = self._data

        for key, value in new_data.items():
            if isinstance(value, Increment):
                # Handle Increment using the actual imported Increment class
                current_value = current_data.get(key, 0)
                current_data[key] = current_value + value.value
            
            # NOTE: For language_distribution, the R-M-W logic in handle_new_interaction
            # ensures we don't need a complex ArrayUnion mock here.
            
            elif merge:
                current_data[key] = value
            else:
                # If not merging, just set the value
                current_data[key] = value

        if not merge: 
            # If not merging, we clear existing data before updating.
            # We preserve increment logic results, as they are implicitly merged.
            temp_data = {}
            for key, value in new_data.items():
                 if not isinstance(value, Increment):
                    temp_data[key] = value
            
            if temp_data:
                self._data.clear()
                self._data.update(temp_data)

class LocalCollection:
    """Mock for a Firestore CollectionReference."""
    def __init__(self, name: str):
        self.name = name
        self._data: Dict = _local_db.setdefault(name, {})

    def document(self, doc_id: str) -> LocalDoc:
        """Mimics col_ref.document(doc_id)."""
        return LocalDoc(doc_id, self._data)

class LocalFirestore:
    """Mock for the Firestore Client."""
    def collection(self, name: str) -> LocalCollection:
        """Mimics db.collection(name)."""
        return LocalCollection(name)

# -----------------------------
# 🔧 GET FIRESTORE CLIENT
# -----------------------------
def get_firestore_client() -> 'Client | LocalFirestore':
    """Get the appropriate Firestore client (Cloud or Local Mock)."""
    if is_local():
        print("Using Local Mock Firestore.")
        return LocalFirestore()
    
    # Cloud environment: use the official client
    return firestore.Client()

# -----------------------------
# 📅 DATE UTILITY
# -----------------------------
def get_week_start_date_str(date: Optional[datetime] = None) -> str:
    """Calculates the date string (YYYYMMDD) for the most recent Monday."""
    if date is None:
        date = datetime.now()
    days_since_monday = date.weekday()
    monday_date = date - timedelta(days=days_since_monday)
    return monday_date.strftime("%Y%m%d")

def generate_log_doc_id(user_id: str, timestamp: datetime) -> str:
    """Generates the custom log document ID: <YYYMMDD><HHMMSS>_<user_id>"""
    time_str = timestamp.strftime("%Y%m%d%H%M%S")
    return f"{time_str}_{user_id}"


# -----------------------------
# 📝 CORE DB ACCESS FUNCTIONS
# -----------------------------

# --- PUBLIC_STATS: overall_summary ---
def get_overall_summary() -> Dict[str, Any]:
    """Retrieves the overall_summary document."""
    db = get_firestore_client()
    doc_ref: DocumentReference = db.collection("public_stats").document("overall_summary")
    snapshot: DocumentSnapshot = doc_ref.get()
    return snapshot.to_dict() if snapshot.exists else {}

def set_overall_summary(data: Dict[str, Any], merge: bool = True):
    """Sets or updates the overall_summary document."""
    db = get_firestore_client()
    doc_ref: DocumentReference = db.collection("public_stats").document("overall_summary")
    doc_ref.set(data, merge=merge)

# --- PUBLIC_STATS: week_YYYYMMDD ---
def get_weekly_stats(week_start_date_str: str) -> Dict[str, Any]:
    """Retrieves the weekly stats document for a given week start date."""
    db = get_firestore_client()
    doc_id = f"week_{week_start_date_str}"
    doc_ref: DocumentReference = db.collection("public_stats").document(doc_id)
    snapshot: DocumentSnapshot = doc_ref.get()
    
    # Initialize basic fields if document doesn't exist 
    if not snapshot.exists:
        return {
            "interactions": 0,  # changed from "interaction_volume"
            "voice": 0,
            "week_start_date": week_start_date_str,
            "language_distribution": []
        }
    return snapshot.to_dict()

def set_weekly_stats(week_start_date_str: str, data: Dict[str, Any], merge: bool = True):
    """Sets or updates the weekly stats document for a given week start date."""
    db = get_firestore_client()
    doc_id = f"week_{week_start_date_str}"
    doc_ref: DocumentReference = db.collection("public_stats").document(doc_id)
    doc_ref.set(data, merge=merge)

# --- LOGS COLLECTION (Custom ID: <YYYMMDD><HHMMSS>_<user_id>) ---
def log_interaction(entry: Dict[str, Any]):
    logging.info("log_interaction entry point")
    db = get_firestore_client()
    logging.info(f"[log_interaction] entry: {entry}")
    user_id = entry.get('user_id')
    timestamp = entry.get('date')
    if not user_id or not timestamp:
        logging.warning("[log_interaction] Missing user_id or date in entry!")
        return
    entry.pop('date')
    log_doc_id = generate_log_doc_id(user_id, timestamp)
    entry_for_db = entry.copy()
    entry_for_db["date"] = SERVER_TIMESTAMP
    logging.info(f"[log_interaction] Writing to logs/{log_doc_id}: {entry_for_db}")
    doc_ref: DocumentReference = db.collection("logs").document(log_doc_id)
    try:
        doc_ref.set(entry_for_db)
        logging.info(f"[log_interaction] Successfully wrote log {log_doc_id}")
    except Exception as e:
        logging.error(f"[log_interaction] Error writing log: {e}")
