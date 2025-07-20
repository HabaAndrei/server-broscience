import firebase_admin
from firebase_admin import credentials, firestore
from config import get_settings
from threading import Lock


class FirestoreAdmin:
    """
    Singleton class to manage Firestore Admin SDK.
    """
    _instance = None
    _lock = Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(FirestoreAdmin, cls).__new__(cls)
                    cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        try:
            settings = get_settings()
            cred = credentials.Certificate({
                "type": settings.google_service_account_type,
                "project_id": settings.google_service_account_project_id,
                "private_key_id": settings.google_service_account_private_key_id,
                "private_key": settings.google_service_account_private_key.replace("\\n", "\n"),
                "client_email": settings.google_service_account_client_email,
                "client_id": settings.google_service_account_client_id,
                "auth_uri": settings.google_service_account_auth_uri,
                "token_uri": settings.google_service_account_token_uri,
                "auth_provider_x509_cert_url": settings.google_service_account_auth_provider_x509_cert_url,
                "client_x509_cert_url": settings.google_service_account_client_x509_cert_url,
                "universe_domain": settings.google_service_account_universe_domain
            })

            firebase_admin.initialize_app(cred)
            self.db = firestore.client()
        except Exception as e:
            print(f"Failed to initialize Firestore Admin: {e}")
            self.db = None

    def insert_data(self, collection_name: str, data: dict, document_id: str = None):
        """
        Insert data into Firestore.

        :param collection_name: Name of the Firestore collection.
        :param data: Dictionary containing the data to insert.
        :param document_id: Optional specific document ID. If None, Firestore generates one.
        :return: The document ID of the inserted data or None on failure.
        """
        try:
            if not self.db:
                raise Exception("Firestore client is not initialized.")

            collection_ref = self.db.collection(collection_name)
            if document_id:
                collection_ref.document(document_id).set(data)
                return document_id
            else:
                doc_ref = collection_ref.add(data)
                generated_id = doc_ref[1].id
                return generated_id
        except Exception as e:
            print(f"Failed to insert data: {e}")
            return None

    def get_data(self, collection_name: str, document_id: str):
        """
        Retrieve a document from Firestore by collection and document ID.

        :param collection_name: Name of the Firestore collection.
        :param document_id: Document ID to retrieve.
        :return: The document data as a dictionary or None if not found or on failure.
        """
        try:
            if not self.db:
                raise Exception("Firestore client is not initialized.")
            doc = self.db.collection(collection_name).document(document_id).get()
            if doc.exists:
                return doc.to_dict()
            else:
                return None
        except Exception as e:
            print(f"Failed to retrieve data: {e}")
            return None
