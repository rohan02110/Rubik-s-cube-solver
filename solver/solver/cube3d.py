import json
import streamlit.components.v1 as components

TEMPLATE = """
<div id="cube-container" style="width:100%;height:500px;"></div>
<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
<script>
(function() {
  const cubeData = __CUBE_DATA__;

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

  // face letter -> function(sticker index 0..8) -> [x, y, z] of the cubie it belongs on
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
  const gap = 1.05;

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
      }
    }
  }
  scene.add(group);

  function animate() {
    requestAnimationFrame(animate);
    controls.update();
    renderer.render(scene, camera);
  }
  animate();
})();
</script>
"""

def render_cube(faces):
    html = TEMPLATE.replace("__CUBE_DATA__", json.dumps(faces))
    components.html(html, height=520)