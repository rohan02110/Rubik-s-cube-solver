import json
import streamlit.components.v1 as components

TEMPLATE = """
<div id="cube-container" style="width:100%;height:500px;"></div>
<div style="margin-top:8px;">
  <button id="prevBtn">◀ Prev</button>
  <span id="moveLabel" style="margin:0 12px;color:white;font-family:monospace;"></span>
  <button id="nextBtn">Next ▶</button>
</div>
<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
<script>
(function() {
  const cubeData = __CUBE_DATA__;
  const moves = __MOVES__;

  const container = document.getElementById('cube-container');
  const scene = new THREE.Scene();
  scene.background = new THREE.Color(0x111111);

  const camera = new THREE.PerspectiveCamera(45, container.clientWidth / 500, 0.1, 100);
  camera.position.set(5, 5, 5);
  camera.lookAt(0, 0, 0);

  const renderer = new THREE.WebGLRenderer({ antialias: true });
  renderer.setSize(container.clientWidth, 500);
  container.appendChild(renderer.domElement);

  const controls = new THREE.OrbitControls(camera, renderer.domElement);

  const light = new THREE.DirectionalLight(0xffffff, 1);
  light.position.set(5, 10, 7);
  scene.add(light);
  scene.add(new THREE.AmbientLight(0x888888));

  const COLORS = {
    White: 0xffffff, Yellow: 0xffff00, Red: 0xff0000,
    Orange: 0xff8800, Green: 0x00aa00, Blue: 0x0044ff,
    black: 0x111111,
  };

  const FACE_POS = {
    U: i => [i % 3 - 1, 1, Math.floor(i / 3) - 1],
    D: i => [i % 3 - 1, -1, 1 - Math.floor(i / 3)],
    F: i => [i % 3 - 1, 1 - Math.floor(i / 3), 1],
    B: i => [1 - i % 3, 1 - Math.floor(i / 3), -1],
    R: i => [1, 1 - Math.floor(i / 3), 1 - i % 3],
    L: i => [-1, 1 - Math.floor(i / 3), i % 3 - 1],
  };

  const stickers = {};
  for (const face of Object.keys(cubeData)) {
    cubeData[face].forEach((colorName, i) => {
      const [x, y, z] = FACE_POS[face](i);
      stickers[`${x}_${y}_${z}_${face}`] = COLORS[colorName] ?? COLORS.black;
    });
  }
  function stickerColor(x, y, z, face) {
    const key = `${x}_${y}_${z}_${face}`;
    return stickers.hasOwnProperty(key) ? stickers[key] : COLORS.black;
  }

  const group = new THREE.Group();
  scene.add(group);
  const gap = 1.05;
  const cubies = [];

  for (let x = -1; x <= 1; x++) {
    for (let y = -1; y <= 1; y++) {
      for (let z = -1; z <= 1; z++) {
        const materials = [
          new THREE.MeshLambertMaterial({ color: x ===  1 ? stickerColor(x, y, z, "R") : COLORS.black }),
          new THREE.MeshLambertMaterial({ color: x === -1 ? stickerColor(x, y, z, "L") : COLORS.black }),
          new THREE.MeshLambertMaterial({ color: y ===  1 ? stickerColor(x, y, z, "U") : COLORS.black }),
          new THREE.MeshLambertMaterial({ color: y === -1 ? stickerColor(x, y, z, "D") : COLORS.black }),
          new THREE.MeshLambertMaterial({ color: z ===  1 ? stickerColor(x, y, z, "F") : COLORS.black }),
          new THREE.MeshLambertMaterial({ color: z === -1 ? stickerColor(x, y, z, "B") : COLORS.black }),
        ];
        const geo = new THREE.BoxGeometry(0.95, 0.95, 0.95);
        const cubie = new THREE.Mesh(geo, materials);
        cubie.position.set(x * gap, y * gap, z * gap);
        group.add(cubie);
        cubies.push(cubie);
      }
    }
  }

  function animate() {
    requestAnimationFrame(animate);
    controls.update();
    renderer.render(scene, camera);
  }
  animate();

  // ---- move logic ----
  const AXIS = { R: 'x', L: 'x', U: 'y', D: 'y', F: 'z', B: 'z' };
  const LAYER = { R: 1, L: -1, U: 1, D: -1, F: 1, B: -1 };
  const CW_SIGN = { R: -1, U: -1, F: -1, L: 1, D: 1, B: 1 };

  function angleFor(move) {
    const letter = move[0];
    const mod = move.slice(1);
    let angle = CW_SIGN[letter] * (Math.PI / 2);
    if (mod === "'") angle = -angle;
    if (mod === "2") angle = angle * 2;
    return angle;
  }

  function inverseMove(move) {
    const letter = move[0];
    const mod = move.slice(1);
    if (mod === "'") return letter;
    if (mod === "2") return move;
    return letter + "'";
  }

  let animating = false;

  function applyMove(move, onDone) {
    const letter = move[0];
    const axis = AXIS[letter];
    const layerVal = LAYER[letter];
    const angle = angleFor(move);

    const affected = cubies.filter(c => Math.round(c.position[axis] / gap) === layerVal);
    const pivot = new THREE.Object3D();
    scene.add(pivot);
    affected.forEach(c => pivot.attach(c));

    animating = true;
    const duration = 250;
    const start = performance.now();

    function step(now) {
      const t = Math.min((now - start) / duration, 1);
      pivot.rotation[axis] = angle * t;
      if (t < 1) {
        requestAnimationFrame(step);
      } else {
        affected.forEach(c => {
          group.attach(c);
          c.position.set(
            Math.round(c.position.x / gap) * gap,
            Math.round(c.position.y / gap) * gap,
            Math.round(c.position.z / gap) * gap
          );
        });
        scene.remove(pivot);
        animating = false;
        onDone && onDone();
      }
    }
    requestAnimationFrame(step);
  }

  // ---- stepper UI ----
  let moveIndex = 0;
  const label = document.getElementById('moveLabel');
  const prevBtn = document.getElementById('prevBtn');
  const nextBtn = document.getElementById('nextBtn');

  function updateLabel() {
    if (moves.length === 0) {
      label.textContent = "Already solved";
    } else {
      label.textContent = moveIndex < moves.length
        ? `Move ${moveIndex} of ${moves.length} — next: ${moves[moveIndex]}`
        : `Move ${moveIndex} of ${moves.length} — done!`;
    }
    prevBtn.disabled = animating || moveIndex === 0;
    nextBtn.disabled = animating || moveIndex >= moves.length;
  }

  nextBtn.addEventListener('click', () => {
    if (animating || moveIndex >= moves.length) return;
    applyMove(moves[moveIndex], () => {
      moveIndex++;
      updateLabel();
    });
  });

  prevBtn.addEventListener('click', () => {
    if (animating || moveIndex === 0) return;
    applyMove(inverseMove(moves[moveIndex - 1]), () => {
      moveIndex--;
      updateLabel();
    });
  });

  updateLabel();
})();
</script>
"""

def render_cube(faces, moves=None):
    html = TEMPLATE.replace("__CUBE_DATA__", json.dumps(faces))
    html = html.replace("__MOVES__", json.dumps(moves or []))
    components.html(html, height=580)