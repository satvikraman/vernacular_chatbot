import os
from app.utils.env import is_local
from google.cloud import firestore

# -----------------------------
# 🔧 LOCAL MOCK DB
# -----------------------------
_local_db = {
    "config": {"PHONE_NUMBER_ID": "727263263792898", "RECIPIENT_WAID": "9880016800"}, 
    "logs": [],
    "metrics": {},
}

class LocalDoc:
    def __init__(self, data):
        self._data = data

    def get(self):
        # mimic Firestore DocumentSnapshot
        class Snap:
            def __init__(self, data):
                self._data = data
            def to_dict(self):
                return self._data
        return Snap(self._data)

    def set(self, new_data, merge=False):
        if merge:
            self._data.update(new_data)
        else:
            self._data.clear()
            self._data.update(new_data)

class LocalCollection:
    def __init__(self, name):
        self.name = name
        self._data = _local_db.setdefault(name, {})

    def document(self, doc_id):
        if doc_id not in self._data:
            self._data[doc_id] = {}
        return LocalDoc(self._data[doc_id])

    def add(self, entry):
        if isinstance(self._data, list):
            self._data.append(entry)
        else:
            # for map-style collections, use a generated ID
            doc_id = str(len(self._data) + 1)
            self._data[doc_id] = entry

class LocalFirestore:
    def collection(self, name):
        return LocalCollection(name)

# -----------------------------
# 🔧 GET FIRESTORE CLIENT
# -----------------------------
def get_firestore_client():
    """Get Firestore client if running in cloud, else local mock."""
    if is_local():
        return LocalFirestore()
    return firestore.Client()

# -----------------------------
# 🔧 CONFIGURATION DOCUMENT
# -----------------------------
def get_bot_config():
    db = get_firestore_client()
    doc_ref = db.collection("config").document("params")
    return doc_ref.get().to_dict()

def update_bot_config(new_config):
    db = get_firestore_client()
    doc_ref = db.collection("config").document("params")
    doc_ref.set(new_config, merge=True)

# -----------------------------
# 📝 LOGGING Q&A
# -----------------------------
def log_conversation(entry):
    db = get_firestore_client()
    db.collection("logs").add(entry)

# -----------------------------
# 📊 METRICS TRACKING
# -----------------------------
def increment_language_count(modality, lang_code):
    db = get_firestore_client()
    doc_ref = db.collection("metrics").document("language_counts")
    if is_local():
        metrics = doc_ref.get().to_dict()
        metrics.setdefault(modality, {})
        metrics[modality][lang_code] = metrics[modality].get(lang_code, 0) + 1
        doc_ref.set(metrics, merge=True)
        return
    field_path = f"{modality}.{lang_code}"
    doc_ref.set({field_path: firestore.Increment(1)}, merge=True)

def get_all_metrics():
    db = get_firestore_client()
    doc_ref = db.collection("metrics").document("language_counts")
    return doc_ref.get().to_dict()
