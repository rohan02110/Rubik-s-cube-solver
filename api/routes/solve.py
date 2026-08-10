import kociemba
from flask import Blueprint, request, jsonify

from solver.cube_solver import build_cubestring

solve_bp = Blueprint('solve', __name__)

@solve_bp.route('/solve', methods=['POST'])
def solve_cube():
    data = request.get_json()
    if not data or 'faces' not in data:
        return jsonify({"error": "Missing 'faces' in request body"}), 400

    faces = data['faces']
    required_faces = {"U", "D", "F", "B", "R", "L"}
    
    # Check that we have all 6 faces, and each has 9 colors
    if not required_faces.issubset(faces.keys()):
        return jsonify({"error": f"Missing faces. Required: {list(required_faces)}"}), 400
        
    for f in required_faces:
        if not isinstance(faces[f], list) or len(faces[f]) != 9:
            return jsonify({"error": f"Face '{f}' must be a list of exactly 9 colors"}), 400

    try:
        cubestring = build_cubestring(faces)
        solution = kociemba.solve(cubestring)
        moves = solution.split()
        return jsonify({
            "moves": moves,
            "move_count": len(moves),
            "cubestring": cubestring
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400
