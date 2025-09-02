import os
from datetime import datetime
from typing import Any, Dict, Optional
from dotenv import load_dotenv
from pymongo import MongoClient
from supabase import create_client
from bson import ObjectId

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY not set in environment")

MONGO_URL = os.getenv("MONGO_URL") or os.getenv("MONGODB_URI") or os.getenv("MONGO_URI")
if not MONGO_URL:
    raise RuntimeError("MONGO_URL is not set in environment")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def _normalize_email(s: Optional[str]) -> Optional[str]:
    if not s:
        return None
    return s.strip().lower()

def _mongo_db():
    client = MongoClient(MONGO_URL)
    return client.get_default_database()

def _pick_latest(rows):
    def ts(x):
        v = x.get("evaluated_at") or x.get("created_at") or x.get("inserted_at")
        try:
            return datetime.fromisoformat(str(v).replace("Z", "+00:00"))
        except Exception:
            return datetime.min
    return max(rows, key=ts) if rows else None

def get_candidate_result(email: str, jd_id: str) -> Optional[Dict[str, Any]]:
    db = _mongo_db()
    cand_col = db["candidates"]
    jd_obj = None
    try:
        jd_obj = ObjectId(jd_id)
    except Exception:
        return None

    cand_doc = cand_col.find_one({"jdId": jd_obj, "email": email})
    if not cand_doc:
        return None

    qs_res = supabase.table("question_sets").select("id").eq("jd_id", jd_id).execute()
    qs_data = qs_res.data or []
    qs_ids = [q["id"] for q in qs_data]
    if not qs_ids:
        return None

    res = supabase.table("test_results").select("*").eq("candidate_email", email).in_("question_set_id", qs_ids).execute()
    rows = res.data or []
    latest = _pick_latest(rows)
    if not latest:
        return None

    return {
        "name": latest.get("candidate_name"),
        "email": cand_doc.get("email"),
        "testId": latest.get("question_set_id"),
        "score": latest.get("score"),
        "maxScore": latest.get("max_score"),
        "percentage": latest.get("percentage"),
        "status": latest.get("status"),
        "tab switches": latest.get("tab_switches"),
        "text selections": latest.get("text_selections"),
        "copies": latest.get("copies"),
        "pastes": latest.get("pastes"),
        "right clicks": latest.get("right_clicks"),
        "face not visible": latest.get("face_not_visible"),
        "inactivities": latest.get("inactivities"),
    }
