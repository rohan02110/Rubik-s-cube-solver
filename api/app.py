import sys
from pathlib import Path

# Add project root to python path to allow importing the 'solver' package
root_path = Path(__file__).resolve().parent.parent
if str(root_path) not in sys.path:
    sys.path.append(str(root_path))

from flask import Flask, jsonify
from flask_cors import CORS

from api.routes.scan import scan_bp
from api.routes.solve import solve_bp
from api.routes.validate import validate_bp

def create_app():
    frontend_folder = root_path / 'frontend' / 'public'
    if frontend_folder.exists():
        app = Flask(__name__, static_folder=str(frontend_folder), static_url_path='')
    else:
        app = Flask(__name__)

    CORS(app)  # Enable CORS for all routes

    app.register_blueprint(scan_bp, url_prefix='/api')
    app.register_blueprint(solve_bp, url_prefix='/api')
    app.register_blueprint(validate_bp, url_prefix='/api')

    @app.route('/api/health', methods=['GET'])
    def health():
        return jsonify({"status": "healthy"}), 200

    @app.route('/', methods=['GET'])
    def index():
        if frontend_folder.exists() and (frontend_folder / 'index.html').exists():
            return app.send_static_file('index.html')
        return jsonify({"message": "Rubik's Cube Solver API is running!"}), 200

    return app

import os

if __name__ == '__main__':
    app = create_app()
    port = int(os.environ.get('PORT', 5000))
    print("\n" + "=" * 65)
    print(f" 📌 OPEN IN BROWSER: http://localhost:{port}")
    print(" ⚠️  Note: Use http://localhost, NOT your IP (10.x.x.x) — browsers")
    print("     block webcam/camera access on non-localhost HTTP addresses.")
    print("=" * 65 + "\n")
    app.run(host='0.0.0.0', port=port, debug=False)