# Rubik's Cube Solver 🧩

An interactive, web-based Rubik's Cube Solver built with a modern **Flask (Python) Backend**, a **Node.js/Express Frontend**, **Three.js**, **OpenCV**, and the **Kociemba Two-Phase Algorithm**.

This application captures your physical Rubik's Cube faces via live camera stream, accurately identifies custom sticker colors in a cylindrical HSV feature space, allows visual verification/editing, and provides an interactive 3D step-by-step solution player.

---

## 🛠️ Tech Stack & Architecture

- **Backend API**: Flask (Python) running on port `5000`
- **Frontend Server & Proxy**: Node.js + Express running on port `3000`
- **Computer Vision & Color Sampling**: OpenCV (`cv2`) & NumPy
- **Solving Engine**: Kociemba Two-Phase Algorithm
- **3D Visualization**: Three.js + OrbitControls

---

## 📂 Project Structure

```
rubiks-solver/
├── api/                         # Flask Backend API
│   ├── app.py                   # Main Flask application entrypoint
│   ├── requirements.txt         # Backend Python dependencies
│   └── routes/                  # API endpoints
│       ├── scan.py              # Camera frame classification endpoint
│       ├── solve.py             # Kociemba solve endpoint
│       └── validate.py          # Pre-solve verification endpoint
├── frontend/                    # Node.js Express Frontend
│   ├── server.js                # Express static server and API proxy
│   ├── package.json             # Frontend Node.js dependencies
│   └── public/                  # SPA client static assets
│       ├── index.html           # Main SPA HTML structure
│       ├── css/
│       │   └── style.css        # Premium dark-mode UI stylesheet
│       └── js/                  # Frontend modules
│           ├── camera.js        # MediaDevices camera API wrapper
│           ├── cube3d.js        # Three.js 3D Interactive cube renderer
│           ├── main.js          # App state machine and UI event coordination
│           ├── scanner.js       # Live scan controller and grid polling
│           └── solver.js        # Solve stage state handler
├── solver/                      # Core Rubik's Solver logic package (Python)
│   ├── __init__.py              # Public package API exports
│   ├── color_classifier.py      # HSV-range color classification
│   ├── config.py                # Scanner rotation sequence and color lists
│   └── cube_solver.py           # Cubestring builder logic
├── tests/                       # Test suite
│   ├── __init__.py
│   └── test_solver.py           # Automated unit tests for solver logic
├── start.ps1                    # One-click startup script (Windows)
└── README.md                    # Project documentation
```

---

## ⚙️ Installation & Local Setup

### 1. Clone the repository
```bash
git clone https://github.com/rohan02110/Rubik-s-cube-solver.git
cd Rubik-s-cube-solver
```

### 2. Startup using PowerShell (Windows)
Simply run the startup script in PowerShell:
```powershell
./start.ps1
```
This script will automatically:
1. Activate the Python virtual environment (`venv`) and install dependencies in `api/requirements.txt`.
2. Install frontend dependencies in `frontend/` and run the development server.
3. Open two terminal instances running both servers.

Once running, navigate to **`http://localhost:3000`** in your browser.

### 3. Manual Startup (Cross-Platform)

#### Run the Flask Backend:
```bash
# Activate virtual environment
source venv/bin/activate # or venv\Scripts\activate on Windows
pip install -r api/requirements.txt
python api/app.py
```
*Backend runs on `http://127.0.0.1:5000`*

#### Run the Node.js Frontend:
```bash
cd frontend
npm install
npm run dev
```
*Frontend runs on `http://localhost:3000`*

---

## 🧪 Running Unit Tests

Run the automated test suite:
```bash
python -m unittest discover -s tests -p "test_*.py"
```

---

## 📜 License

Distributed under the MIT License. See `LICENSE` for details.
