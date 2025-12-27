import json
import uuid
from datetime import datetime, timedelta

from firebase_admin import auth, firestore, initialize_app
from firebase_functions import https_fn, options

# Initialize Firebase
app = initialize_app()
db = firestore.client()

# CORS configuration
cors_options = options.CorsOptions(
    allow_origins=["http://localhost:3000", "https://app.seomcp.run"],
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["Content-Type", "Authorization"],
)


def _unauthorized(message: str = "Unauthorized"):
    return https_fn.Response(
        json.dumps({"error": message}), status=401, mimetype="application/json"
    )


def _error(message: str, code: int = 500):
    return https_fn.Response(
        json.dumps({"error": message}), status=code, mimetype="application/json"
    )


def _verify_user(req: https_fn.Request):
    auth_header = req.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise auth.InvalidIdTokenError("Missing bearer token")
    id_token = auth_header[7:]
    claims = auth.verify_id_token(id_token)
    uid = claims.get("uid")
    if not uid:
        raise auth.InvalidIdTokenError("Invalid token")
    return uid


@https_fn.on_request(cors=cors_options)
def generate_api_key(req: https_fn.Request) -> https_fn.Response:
    """Generate a new API key for authenticated user."""
    try:
        uid = _verify_user(req)
        api_key = f"sk_{uuid.uuid4().hex}"
        expires_at = datetime.utcnow() + timedelta(days=90)

        user_ref = db.collection("users").document(uid)
        keys_ref = user_ref.collection("api_keys")
        keys_ref.document(api_key[:20]).set(
            {
                "key": api_key,
                "created_at": datetime.utcnow(),
                "expires_at": expires_at,
                "last_used": None,
                "calls_count": 0,
            }
        )
        return https_fn.Response(
            json.dumps({"api_key": api_key, "expires_at": expires_at.isoformat()}),
            status=200,
            mimetype="application/json",
        )
    except auth.InvalidIdTokenError:
        return _unauthorized("Invalid token")
    except Exception as e:  # noqa: BLE001
        return _error(str(e))


@https_fn.on_request(cors=cors_options)
def list_api_keys(req: https_fn.Request) -> https_fn.Response:
    """List API keys for authenticated user."""
    try:
        uid = _verify_user(req)
        user_ref = db.collection("users").document(uid)
        keys_ref = user_ref.collection("api_keys")
        docs = keys_ref.stream()
        keys = []
        for doc in docs:
            data = doc.to_dict()
            keys.append(
                {
                    "id": doc.id,
                    "key": f"{data.get('key', '')[:20]}...",
                    "created_at": data.get("created_at").isoformat()
                    if data.get("created_at")
                    else None,
                    "expires_at": data.get("expires_at").isoformat()
                    if data.get("expires_at")
                    else None,
                    "calls_count": data.get("calls_count", 0),
                }
            )
        return https_fn.Response(
            json.dumps({"keys": keys}), status=200, mimetype="application/json"
        )
    except auth.InvalidIdTokenError:
        return _unauthorized("Invalid token")
    except Exception as e:  # noqa: BLE001
        return _error(str(e))


@https_fn.on_request(cors=cors_options)
def delete_api_key(req: https_fn.Request) -> https_fn.Response:
    """Delete an API key."""
    try:
        uid = _verify_user(req)
        key_id = req.args.get("id")
        if not key_id:
            return _error("Missing key id", 400)
        user_ref = db.collection("users").document(uid)
        user_ref.collection("api_keys").document(key_id).delete()
        return https_fn.Response(
            json.dumps({"message": "Key deleted"}), status=200, mimetype="application/json"
        )
    except auth.InvalidIdTokenError:
        return _unauthorized("Invalid token")
    except Exception as e:  # noqa: BLE001
        return _error(str(e))
