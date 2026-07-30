import streamlit as st
import streamlit.components.v1 as components

st.title("3D Cube Test")

cube_html = """
<div id="cube-container" style="width:100%;height:500px;"></div>
<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
<script>
(function() {
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

  // solved cube reference: face letter -> color name
  const solved = { U: "White", D: "Yellow", F: "Green", B: "Blue", R: "Red", L: "Orange" };

  const group = new THREE.Group();
  const gap = 1.05;

  for (let x = -1; x <= 1; x++) {
    for (let y = -1; y <= 1; y++) {
      for (let z = -1; z <= 1; z++) {
        const materials = [
          new THREE.MeshLambertMaterial({ color: x ===  1 ? COLORS[solved.R] : COLORS.black }), // +x
          new THREE.MeshLambertMaterial({ color: x === -1 ? COLORS[solved.L] : COLORS.black }), // -x
          new THREE.MeshLambertMaterial({ color: y ===  1 ? COLORS[solved.U] : COLORS.black }), // +y
          new THREE.MeshLambertMaterial({ color: y === -1 ? COLORS[solved.D] : COLORS.black }), // -y
          new THREE.MeshLambertMaterial({ color: z ===  1 ? COLORS[solved.F] : COLORS.black }), // +z
          new THREE.MeshLambertMaterial({ color: z === -1 ? COLORS[solved.B] : COLORS.black }), // -z
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

components.html(cube_html, height=520)