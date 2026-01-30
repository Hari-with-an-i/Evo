import firebase_admin
from firebase_admin import credentials, firestore
import datetime

# --- Initialize Firebase Admin SDK ---
# This setup needs to run only once.
try:
    cred = credentials.Certificate("firebase-credentials.json")
    firebase_admin.initialize_app(cred)
    print("✅ Firebase App initialized.")
except ValueError:
    print("⚠️ Firebase App already initialized.")
    pass

# Get a reference to the Firestore database
db = firestore.client()

def tool_save_analysis(analysis_data: dict) -> str:
    """
    Saves the complete analysis JSON to a new document in Firestore.

    Args:
        analysis_data (dict): The final JSON data from the workflow.

    Returns:
        str: The ID of the newly created document.
    """
    print("💾 Using Firestore Tool to save data...")
    try:
        # Create a reference to the collection. It will be created if it doesn't exist.
        collection_ref = db.collection('analysis_results')

        # Add a timestamp to the data for tracking
        analysis_data['created_at'] = datetime.datetime.now(datetime.timezone.utc)

        # Add a new document with an auto-generated ID
        update_time, doc_ref = collection_ref.add(analysis_data)

        print(f"✅ Data saved successfully. Document ID: {doc_ref.id}")
        return doc_ref.id
    except Exception as e:
        print(f"❌ Error saving to Firestore: {e}")
        return None

def tool_fetch_analysis(document_id: str) -> dict:
    """
    Fetches a previously saved analysis document from Firestore.
    """
    print(f"🔍 Using Firestore Tool to fetch document: {document_id}")
    try:
        doc_ref = db.collection('analysis_results').document(document_id)
        doc = doc_ref.get()
        if doc.exists:
            print("✅ Document found.")
            return doc.to_dict()
        else:
            print("❌ Document not found.")
            return None
    except Exception as e:
        print(f"❌ Error fetching from Firestore: {e}")
        return None