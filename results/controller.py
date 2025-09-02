from flask import Blueprint, request, jsonify
from services.result_services_db import get_candidate_result

bp = Blueprint("results", __name__)

@bp.route("/candidate_result")
def candidate_result():
    email = request.args.get("email")
    jd_id = request.args.get("jd_id")
    if not email or not jd_id:
        return jsonify({"error": "Missing email or jd_id"}), 400

    result = get_candidate_result(email, jd_id)
    if not result:
        return jsonify({"error": "No result found"}), 404
    return jsonify(result)
