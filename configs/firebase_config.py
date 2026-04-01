import os

import firebase_admin
from dotenv import load_dotenv
from firebase_admin import credentials, storage

_firebase_initialized = False

# Load .env so Firebase settings are available
load_dotenv()


def initialize_firebase():
    """Khoi tao Firebase Admin SDK"""
    global _firebase_initialized

    if _firebase_initialized:
        return

    try:
        # Service account path (configurable via env)
        service_account_path = os.getenv("FIREBASE_SERVICE_ACCOUNT", "serviceAccountKey.json")
        if not os.path.exists(service_account_path):
            raise FileNotFoundError(
                f"Khong tim thay service account key: {service_account_path}"
            )

        # Bucket name from env. If only project_id exists, infer default bucket.
        bucket_name = os.getenv("FIREBASE_STORAGE_BUCKET")
        project_id = os.getenv("FIREBASE_PROJECT_ID")
        if not bucket_name and project_id:
            bucket_name = f"{project_id}.appspot.com"

        if not bucket_name:
            raise ValueError(
                "Thieu cau hinh FIREBASE_STORAGE_BUCKET (vi du: my-project-id.appspot.com)"
            )

        cred = credentials.Certificate(service_account_path)

        firebase_admin.initialize_app(cred, {
            "storageBucket": bucket_name
        })

        _firebase_initialized = True
        print("✓ Firebase initialized successfully")
    except Exception as e:
        print(f"✗ Firebase initialization failed: {str(e)}")
        raise


def get_storage_bucket():
    """Lay Firebase Storage bucket"""
    if not _firebase_initialized:
        initialize_firebase()
    return storage.bucket()
