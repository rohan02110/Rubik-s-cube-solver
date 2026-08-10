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
    app = Flask(__name__)
    CORS(app)  # Enable CORS for all routes

    app.register_blueprint(scan_bp, url_prefix='/api')
    app.register_blueprint(solve_bp, url_prefix='/api')
    app.register_blueprint(validate_bp, url_prefix='/api')

    @app.route('/api/health', methods=['GET'])
    def health():
        return jsonify({"status": "healthy"}), 200

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host='10.247.204.229', port=5000, debug=True)
