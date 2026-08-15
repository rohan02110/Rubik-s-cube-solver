import { captureFrame } from './camera.js';
import { state, SCAN_ORDER, COLOR_NAMES, renderMiniGrid } from './main.js';

let pollInterval = null;
let isProcessingFrame = false;
let animationFrameId = null;

/**
 * Starts polling the camera, sending frames to Flask, and rendering the scan UI.
 * @param {HTMLVideoElement} videoEl
 * @param {HTMLCanvasElement} canvasEl
 * @param {HTMLCanvasElement} overlayCanvasEl
 * @param {HTMLElement} gridContainerEl
 */
export function startScanning(videoEl, canvasEl, overlayCanvasEl, gridContainerEl) {
  if (pollInterval) {
    clearInterval(pollInterval);
  }
  stopOverlayLoop();

  isProcessingFrame = false;

  // Start the client-side continuous overlay draw loop
  startOverlayLoop(videoEl, overlayCanvasEl);

  pollInterval = setInterval(async () => {
    if (isProcessingFrame) return;
    isProcessingFrame = true;

    try {
      const blob = await captureFrame(videoEl, canvasEl);
      const formData = new FormData();
      formData.append('frame', blob, 'frame.jpg');

      // Append custom color legend if calibrated
      if (state.isCalibrated && state.legend) {
        formData.append('legend', JSON.stringify(state.legend));
      }

      const response = await fetch('/api/scan-frame', {
        method: 'POST',
        body: formData
      });

      if (!response.ok) {
        throw new Error("Failed to scan frame");
      }

      const result = await response.json();
      state.liveDetected = result.colors;
      if (result.hsv) {
        state.liveHsv = result.hsv;
      }

    } catch (err) {
      console.warn("Scanning frame error:", err);
    } finally {
      isProcessingFrame = false;
    }
  }, 250); // Poll every 250ms for low latency
}

/**
 * Stops scanning and polling.
 */
export function stopScanning() {
  if (pollInterval) {
    clearInterval(pollInterval);
    pollInterval = null;
  }
  stopOverlayLoop();
}

/**
 * Starts the requestAnimationFrame loop to render the grid overlay locally.
 */
function startOverlayLoop(videoEl, overlayCanvasEl) {
  const draw = () => {
    if (!pollInterval) return; // stopped scanning

    const width = videoEl.clientWidth;
    const height = videoEl.clientHeight;

    // Keep canvas matching the client layout size for high-DPI/responsive scaling
    if (overlayCanvasEl.width !== width || overlayCanvasEl.height !== height) {
      overlayCanvasEl.width = width;
      overlayCanvasEl.height = height;
    }

    drawOverlay(overlayCanvasEl, state.liveDetected);
    animationFrameId = requestAnimationFrame(draw);
  };
  animationFrameId = requestAnimationFrame(draw);
}

/**
 * Stops the requestAnimationFrame loop.
 */
function stopOverlayLoop() {
  if (animationFrameId) {
    cancelAnimationFrame(animationFrameId);
    animationFrameId = null;
  }
}

/**
 * Renders the 3x3 grid, dimming overlay, and color indicator badges on the canvas.
 * @param {HTMLCanvasElement} canvasEl
 * @param {Array<string>} colors
 */
export function drawOverlay(canvasEl, colors) {
  const ctx = canvasEl.getContext('2d');
  const w = canvasEl.width;
  const h = canvasEl.height;

  ctx.clearRect(0, 0, w, h);
  if (!w || !h) return;

  const size = Math.min(w, h);
  const x0 = (w - size) / 2;
  const y0 = (h - size) / 2;
  const cell = size / 3;

  // 1. Dim the areas outside the 3x3 scan grid
  ctx.fillStyle = 'rgba(0, 0, 0, 0.45)';
  // Top
  ctx.fillRect(0, 0, w, y0);
  // Bottom
  ctx.fillRect(0, y0 + size, w, h - (y0 + size));
  // Left
  ctx.fillRect(0, y0, x0, size);
  // Right
  ctx.fillRect(x0 + size, y0, w - (x0 + size), size);

  // 2. Draw the main grid outline
  ctx.strokeStyle = '#ffffff';
  ctx.lineWidth = 3;
  ctx.strokeRect(x0, y0, size, size);

  // 3. Draw grid inner divider lines
  ctx.strokeStyle = 'rgba(255, 255, 255, 0.4)';
  ctx.lineWidth = 1.5;
  for (let i = 1; i < 3; i++) {
    // Vertical line
    ctx.beginPath();
    ctx.moveTo(x0 + i * cell, y0);
    ctx.lineTo(x0 + i * cell, y0 + size);
    ctx.stroke();

    // Horizontal line
    ctx.beginPath();
    ctx.moveTo(x0, y0 + i * cell);
    ctx.lineTo(x0 + size, y0 + i * cell);
    ctx.stroke();
  }

  // 4. Draw color overlay blocks in the center of each cell
  if (!colors || colors.length !== 9) return;

  const OVERLAY_COLORS = {
    "White":  "rgba(255, 255, 255, 0.85)",
    "Yellow": "rgba(255, 235, 59, 0.85)",
    "Red":    "rgba(244, 67, 54, 0.85)",
    "Orange": "rgba(255, 152, 0, 0.85)",
    "Green":  "rgba(76, 175, 80, 0.85)",
    "Blue":   "rgba(33, 150, 243, 0.85)",
  };

  const TEXT_COLORS = {
    "White":  "#212121",
    "Yellow": "#212121",
    "Red":    "#ffffff",
    "Orange": "#ffffff",
    "Green":  "#ffffff",
    "Blue":   "#ffffff",
  };

  const sq = Math.max(12, cell / 5); // half-width of the indicator block

  for (let row = 0; row < 3; row++) {
    for (let col = 0; col < 3; col++) {
      const idx = row * 3 + col;
      const colorName = colors[idx] || "White";

      const cx = x0 + col * cell + cell / 2;
      const cy = y0 + row * cell + cell / 2;

      const fillStyle = OVERLAY_COLORS[colorName] || "rgba(158, 158, 158, 0.85)";
      const textColor = TEXT_COLORS[colorName] || "#ffffff";

      // Colored rectangle
      ctx.fillStyle = fillStyle;
      ctx.fillRect(cx - sq, cy - sq, sq * 2, sq * 2);

      // Border around rectangle
      ctx.strokeStyle = 'rgba(0, 0, 0, 0.25)';
      ctx.lineWidth = 1;
      ctx.strokeRect(cx - sq, cy - sq, sq * 2, sq * 2);

      // Letter inside rectangle
      ctx.fillStyle = textColor;
      ctx.font = `bold ${Math.max(11, sq * 1.1)}px Outfit, sans-serif`;
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillText(colorName[0], cx, cy);
    }
  }
}

/**
 * Renders the 3x3 interactive verification grid based on live colors and user corrections.
 * @param {HTMLElement} container
 */
export function renderVerificationGrid(container) {
  container.innerHTML = '';
  const currentFace = SCAN_ORDER[state.currentFaceIndex];
  const corrs = state.corrections[currentFace] || {};
  
  for (let i = 0; i < 9; i++) {
    const defaultColor = state.snapshotColors[i] || "White";
    const color = corrs[i] || defaultColor;

    const cell = document.createElement('div');
    cell.className = 'grid-cell';
    cell.dataset.color = color;
    cell.dataset.index = i;
    cell.textContent = color[0]; // first letter (W, Y, R, O, G, B)

    cell.onclick = () => {
      const currentColor = color;
      const nextIndex = (COLOR_NAMES.indexOf(currentColor) + 1) % COLOR_NAMES.length;
      const nextColor = COLOR_NAMES[nextIndex];
      
      if (!state.corrections[currentFace]) {
        state.corrections[currentFace] = {};
      }
      state.corrections[currentFace][i] = nextColor;
      
      // Re-render immediately to reflect clicked change
      renderVerificationGrid(container);
    };

    container.appendChild(cell);
  }
}

/**
 * Updates the completed faces list in the UI.
 * @param {HTMLElement} listContainer
 * @param {HTMLElement} sectionContainer
 */
export function updateCompletedFacesUI(listContainer, sectionContainer) {
  const completedKeys = Object.keys(state.faces);
  if (completedKeys.length === 0) {
    sectionContainer.style.display = 'none';
    return;
  }

  sectionContainer.style.display = 'block';
  listContainer.innerHTML = '';

  completedKeys.forEach((face) => {
    const row = document.createElement('div');
    row.className = 'completed-face-row';

    const label = document.createElement('span');
    label.innerHTML = `<strong>Face ${face}</strong>`;
    row.appendChild(label);

    const miniGrid = renderMiniGrid(state.faces[face]);
    row.appendChild(miniGrid);

    listContainer.appendChild(row);
  });
}
