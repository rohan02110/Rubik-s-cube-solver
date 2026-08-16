let currentInstance = null;

/**
 * Initializes the 3D cube model inside a DOM container with step-by-step solver navigation.
 * @param {HTMLElement} container
 * @param {object} cubeData
 * @param {Array<string>} moves
 */
export function renderCube(container, cubeData, moves) {
  // Clear any existing WebGL or content in the container
  container.innerHTML = '';

  // Setup elements inside container
  const canvasContainer = document.createElement('div');
  canvasContainer.style.width = '100%';
  canvasContainer.style.height = '100%';
  container.appendChild(canvasContainer);

  const scene = new THREE.Scene();
  scene.background = new THREE.Color(0x111111);

  const camera = new THREE.PerspectiveCamera(45, canvasContainer.clientWidth / canvasContainer.clientHeight, 0.1, 100);
  camera.position.set(5, 5, 5);
  camera.lookAt(0, 0, 0);

  const renderer = new THREE.WebGLRenderer({ antialias: true });
  renderer.setSize(canvasContainer.clientWidth, canvasContainer.clientHeight);
  canvasContainer.appendChild(renderer.domElement);

  const controls = new THREE.OrbitControls(camera, renderer.domElement);
  controls.enableDamping = true;
  controls.dampingFactor = 0.05;

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

  let animationFrameId;
  function animate() {
    animationFrameId = requestAnimationFrame(animate);
    controls.update();
    renderer.render(scene, camera);
  }
  animate();

  // Handle container resizing
  const resizeObserver = new ResizeObserver(() => {
    if (canvasContainer.clientWidth && canvasContainer.clientHeight) {
      camera.aspect = canvasContainer.clientWidth / canvasContainer.clientHeight;
      camera.updateProjectionMatrix();
      renderer.setSize(canvasContainer.clientWidth, canvasContainer.clientHeight);
    }
  });
  resizeObserver.observe(canvasContainer);

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
  let isPlaying = false;
  let playTimeoutId = null;

  function easeInOutQuad(t) {
    return t < 0.5 ? 2 * t * t : -1 + (4 - 2 * t) * t;
  }

  function applyMove(move, duration = 300, onDone) {
    const letter = move[0];
    const axis = AXIS[letter];
    const layerVal = LAYER[letter];
    const angle = angleFor(move);

    const affected = cubies.filter(c => Math.round(c.position[axis] / gap) === layerVal);
    const pivot = new THREE.Object3D();
    scene.add(pivot);
    affected.forEach(c => pivot.attach(c));

    animating = true;
    const start = performance.now();

    function step(now) {
      const rawT = Math.min((now - start) / duration, 1);
      const easedT = easeInOutQuad(rawT);
      pivot.rotation[axis] = angle * easedT;

      if (rawT < 1) {
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
        if (onDone) onDone();
      }
    }
    requestAnimationFrame(step);
  }

  // Stepper UI hookups
  let moveIndex = 0;
  const moveLabel = document.getElementById('move-label');
  const prevBtn = document.getElementById('prev-move-btn');
  const nextBtn = document.getElementById('next-move-btn');
  const playBtn = document.getElementById('play-moves-btn');
  const resetBtn = document.getElementById('reset-moves-btn');

  function updateLabel() {
    if (moves.length === 0) {
      if (moveLabel) moveLabel.textContent = "Already solved";
    } else {
      if (moveLabel) {
        moveLabel.textContent = moveIndex < moves.length
          ? `Move ${moveIndex + 1} of ${moves.length} — Next: ${moves[moveIndex]}`
          : `Completed (${moves.length}/${moves.length} moves) 🎉`;
      }
    }

    if (prevBtn) prevBtn.disabled = animating || moveIndex === 0;
    if (nextBtn) nextBtn.disabled = animating || moveIndex >= moves.length;
    if (resetBtn) resetBtn.disabled = animating || moveIndex === 0;

    if (playBtn) {
      playBtn.disabled = moves.length === 0 || (moveIndex >= moves.length && !isPlaying);
      playBtn.textContent = isPlaying ? "⏸ Pause" : "▶ Auto Play";
      if (isPlaying) {
        playBtn.classList.remove('btn-primary');
        playBtn.classList.add('btn-secondary');
      } else {
        playBtn.classList.remove('btn-secondary');
        playBtn.classList.add('btn-primary');
      }
    }
  }

  const stopAutoPlay = () => {
    isPlaying = false;
    if (playTimeoutId) {
      clearTimeout(playTimeoutId);
      playTimeoutId = null;
    }
    updateLabel();
  };

  const playStep = () => {
    if (!isPlaying || moveIndex >= moves.length) {
      stopAutoPlay();
      return;
    }

    nextHandler(() => {
      if (isPlaying && moveIndex < moves.length) {
        playTimeoutId = setTimeout(playStep, 250);
      } else {
        stopAutoPlay();
      }
    });
  };

  const nextHandler = (callback) => {
    if (animating || moveIndex >= moves.length) return;
    applyMove(moves[moveIndex], 300, () => {
      moveIndex++;
      updateLabel();
      if (typeof callback === 'function') callback();
    });
  };

  const prevHandler = () => {
    if (isPlaying) stopAutoPlay();
    if (animating || moveIndex === 0) return;
    applyMove(inverseMove(moves[moveIndex - 1]), 300, () => {
      moveIndex--;
      updateLabel();
    });
  };

  const playHandler = () => {
    if (isPlaying) {
      stopAutoPlay();
    } else {
      if (moveIndex >= moves.length) {
        // Rewind to start if at the end
        resetHandler();
      }
      isPlaying = true;
      updateLabel();
      playStep();
    }
  };

  const resetHandler = () => {
    if (isPlaying) stopAutoPlay();
    if (animating) return;
    // Fast render recreation to return to 0 index
    renderCube(container, cubeData, moves);
  };

  if (prevBtn) prevBtn.onclick = prevHandler;
  if (nextBtn) nextBtn.onclick = () => { if (isPlaying) stopAutoPlay(); nextHandler(); };
  if (playBtn) playBtn.onclick = playHandler;
  if (resetBtn) resetBtn.onclick = resetHandler;

  updateLabel();

  // Clear previous instance
  if (currentInstance) {
    cancelAnimationFrame(currentInstance.animationFrameId);
    currentInstance.resizeObserver.disconnect();
  }

  currentInstance = {
    animationFrameId,
    resizeObserver,
    destroy: () => {
      if (isPlaying) stopAutoPlay();
      cancelAnimationFrame(animationFrameId);
      resizeObserver.disconnect();
    }
  };
}
