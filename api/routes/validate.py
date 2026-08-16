from collections import Counter
from flask import Blueprint, request, jsonify

from solver.config import COLOR_NAMES
from solver.cube_solver import STRING_ORDER

validate_bp = Blueprint('validate', __name__)

@validate_bp.route('/validate', methods=['GET', 'POST'])
def validate_cube():
    if request.method == 'GET':
        return jsonify({
            "status": "active",
            "endpoint": "/api/validate",
            "message": "The /api/validate endpoint requires an HTTP POST request containing scanned cube face data."
        }), 200

    data = request.get_json()
    if not data or 'faces' not in data:
        return jsonify({"valid": False, "error": "Missing 'faces' in request body"}), 400

    faces = data['faces']
    required_faces = {"U", "D", "F", "B", "R", "L"}
    
    # 1. Check all faces are present and have 9 items
    if not required_faces.issubset(faces.keys()):
        return jsonify({
            "valid": False,
            "error": f"Missing faces. Scanned faces: {list(faces.keys())}"
        }), 200

    for f in required_faces:
        if not isinstance(faces[f], list) or len(faces[f]) != 9:
            return jsonify({
                "valid": False,
                "error": f"Face '{f}' does not have exactly 9 stickers."
            }), 200

    # 2. Check center colors uniqueness
    centers = [faces[f][4] for f in STRING_ORDER]
    if len(set(centers)) != 6:
        dup_centers = [c for c, count in Counter(centers).items() if count > 1]
        return jsonify({
            "valid": False,
            "error": f"Duplicate center colors found: {', '.join(dup_centers)}. Each face center must be a unique color."
        }), 200

    # 3. Check that all colors are valid and mapped to center colors
    color_to_face = dict(zip(centers, STRING_ORDER))
    all_stickers = [color for f in required_faces for color in faces[f]]
    
    invalid_colors = [c for c in all_stickers if c not in color_to_face]
    if invalid_colors:
        unique_invalid = list(set(invalid_colors))
        return jsonify({
            "valid": False,
            "error": f"Color(s) {', '.join(unique_invalid)} are present on stickers but do not match the center color of any face."
        }), 200

    # 4. Check that each color appears exactly 9 times
    counts = Counter(all_stickers)
    miscounts = []
    for color, count in counts.items():
        if count != 9:
            miscounts.append(f"{color} appears {count} times (expected 9)")
            
    if miscounts:
        return jsonify({
            "valid": False,
            "error": f"Sticker count mismatch: {'; '.join(miscounts)}. Check for misread colors."
        }), 200

    return jsonify({"valid": True}), 200
