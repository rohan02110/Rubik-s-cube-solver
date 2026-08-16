import { startCamera, stopCamera } from './camera.js';
import { startScanning, stopScanning, renderVerificationGrid, updateCompletedFacesUI } from './scanner.js';
import { solveCube } from './solver.js';

// Standard rotation order for capturing cube faces
export const SCAN_ORDER = ["F", "R", "B", "L", "U", "D"];

// Standard sticker color palette names
export const COLOR_NAMES = ["White", "Yellow", "Red", "Orange", "Green", "Blue"];

// Step-by-step physical cube rotation instructions for the user
export const INSTRUCTIONS = {
  "F": "Hold the cube naturally in front of you. Whatever face points at you now is your reference Front (F) — you'll return to this exact pose twice more.",
  "R": "Without tilting up or down, spin the cube 90° to your right so the face that was on the right now points at you.",
  "B": "Spin another 90° in the same direction.",
  "L": "Spin another 90° in the same direction — last spin.",
  "U": "Return to the Front-facing pose from step 1. Tilt the cube backward (top rolls away from you) 90°, so the top face points at the camera.",
  "D": "From the Front-facing pose again, tilt the cube forward (top rolls toward you) 90°, so the bottom face points at the camera."
};

// Global App State
export const state = {
  stage: "scan", // "scan" | "solve" | "reverify"
  faces: {}, // Stores locked colors for each face key, e.g. { "F": [...] }
  currentFaceIndex: 0,
  corrections: {}, // Manual user corrections per face: { "F": { 0: "Yellow" } }
  liveDetected: Array(9).fill("White"), // Live frame sample classifications
  liveHsv: Array(9).fill([0, 0, 0]), // Live frame raw HSV values
  snapshotColors: Array(9).fill("White"), // Snapshot of colors copied for verification
  reverifyFace: "F", // Face being re-verified
  reverifyColors: Array(9).fill("White") // 9 colors being edited in re-verify view
};

// DOM Cache
let videoEl, canvasEl, overlayCanvasEl, gridContainerEl, lockBtn, resetBtn, scanStageSection, solveStageSection;
let progressText, progressFill, faceHeader, instructionBox, scanTriggerBtn;
let rescanSelect, rescanSingleBtn, scanAllBtn, completedList, completedSection;

// Re-verify DOM Cache
let reverifySingleBtn, reverifyStageSection, reverifyFaceTitle, reverifyGridEl, saveReverifyBtn, cancelReverifyBtn;

window.addEventListener('DOMContentLoaded', async () => {
  // DOM Cache init
  videoEl = document.getElementById('camera-video');
  canvasEl = document.getElementById('capture-canvas');
  overlayCanvasEl = document.getElementById('overlay-canvas');
  gridContainerEl = document.getElementById('verification-grid');
  lockBtn = document.getElementById('lock-face-btn');
  resetBtn = document.getElementById('reset-scan-btn');
  scanStageSection = document.getElementById('scan-stage');
  solveStageSection = document.getElementById('solve-stage');
  scanTriggerBtn = document.getElementById('scan-trigger-btn');
  
  progressText = document.getElementById('scan-progress-text');
  progressFill = document.getElementById('scan-progress-fill');
  faceHeader = document.getElementById('current-face-header');
  instructionBox = document.getElementById('instruction-box');
  
  rescanSelect = document.getElementById('rescan-face-select');
  rescanSingleBtn = document.getElementById('rescan-single-btn');
  scanAllBtn = document.getElementById('scan-all-btn');
  
  completedList = document.getElementById('completed-faces-list');
  completedSection = document.getElementById('completed-faces-section');

  // Re-verify DOM Cache init
  reverifySingleBtn = document.getElementById('reverify-single-btn');
  reverifyStageSection = document.getElementById('reverify-stage');
  reverifyFaceTitle = document.getElementById('reverify-face-title');
  reverifyGridEl = document.getElementById('reverify-grid');
  saveReverifyBtn = document.getElementById('save-reverify-btn');
  cancelReverifyBtn = document.getElementById('cancel-reverify-btn');

  // Event Handlers Setup
  lockBtn.onclick = handleLockFace;
  resetBtn.onclick = handleResetScan;
  scanAllBtn.onclick = handleResetScan;
  rescanSingleBtn.onclick = handleRescanSingleFace;
  scanTriggerBtn.onclick = handleScanTrigger;

  // Re-verify Event Handlers
  if (reverifySingleBtn) reverifySingleBtn.onclick = handleReverifySingleFace;
  if (saveReverifyBtn) saveReverifyBtn.onclick = handleSaveReverify;
  if (cancelReverifyBtn) cancelReverifyBtn.onclick = handleCancelReverify;

  // Initialize UI
  updateProgressUI();
  await initScanStage();
});

export async function initScanStage() {
  state.stage = "scan";
  solveStageSection.classList.remove('active');
  if (reverifyStageSection) reverifyStageSection.classList.remove('active');
  scanStageSection.classList.add('active');
  
  // Disable lock button until user manual triggers scan
  lockBtn.disabled = true;
  
  // Reset snapshot colors to a default blank/white state
  state.snapshotColors = Array(9).fill("White");
  renderVerificationGrid(gridContainerEl);

  // Update header and instruction text
  const currentFace = SCAN_ORDER[state.currentFaceIndex];
  faceHeader.innerHTML = `Face ${state.currentFaceIndex + 1} / 6 — <strong>${currentFace}</strong>`;
  instructionBox.className = 'alert alert-info';
  instructionBox.textContent = INSTRUCTIONS[currentFace];
  lockBtn.textContent = `✅ Lock in Face ${currentFace}`;

  // Start Camera and Scan Loop
  try {
    await startCamera(videoEl);
    startScanning(videoEl, canvasEl, overlayCanvasEl, gridContainerEl);
  } catch (err) {
    console.error("Camera start failed:", err);
    instructionBox.className = 'alert alert-danger';
    instructionBox.innerHTML = `<strong>Camera Error:</strong> ${err.message}. Please grant camera access and reload.`;
  }
  
  updateCompletedFacesUI(completedList, completedSection);
}

function handleScanTrigger() {
  const currentFace = SCAN_ORDER[state.currentFaceIndex];
  // Copy live detected colors to snapshot colors
  state.snapshotColors = [...state.liveDetected];
  // Clear any previous manual corrections to start fresh with new scan
  state.corrections[currentFace] = {};
  
  renderVerificationGrid(gridContainerEl);
  lockBtn.disabled = false; // Enable lock button now that we have scanned colors
}

function handleLockFace() {
  const currentFace = SCAN_ORDER[state.currentFaceIndex];
  const corrs = state.corrections[currentFace] || {};
  
  // Merge snapshot colors with manual corrections
  const finalColors = [];
  for (let i = 0; i < 9; i++) {
    finalColors.push(corrs[i] || state.snapshotColors[i] || "White");
  }
  
  state.faces[currentFace] = finalColors;
  
  // Advance to next face or solve
  if (Object.keys(state.faces).length === 6) {
    switchToSolveStage();
  } else {
    // Find next unscanned face index
    let nextIndex = state.currentFaceIndex + 1;
    while (nextIndex < SCAN_ORDER.length && state.faces[SCAN_ORDER[nextIndex]]) {
      nextIndex++;
    }
    if (nextIndex >= SCAN_ORDER.length) {
      // Find first unscanned face
      nextIndex = SCAN_ORDER.findIndex(f => !state.faces[f]);
    }
    
    state.currentFaceIndex = nextIndex;
    updateProgressUI();
    initScanStage();
  }
}

function handleResetScan() {
  stopScanning();
  stopCamera();
  
  state.faces = {};
  state.currentFaceIndex = 0;
  state.corrections = {};
  state.liveDetected = Array(9).fill("White");
  state.snapshotColors = Array(9).fill("White");
  
  updateProgressUI();
  initScanStage();
}

function handleRescanSingleFace() {
  const targetFace = rescanSelect.value;
  stopScanning();
  stopCamera();
  
  // Remove the face from scanned list
  delete state.faces[targetFace];
  delete state.corrections[targetFace];
  
  // Set current face index to target face
  state.currentFaceIndex = SCAN_ORDER.indexOf(targetFace);
  
  updateProgressUI();
  initScanStage();
}

function handleReverifySingleFace() {
  const targetFace = rescanSelect.value;
  if (!state.faces[targetFace]) {
    state.faces[targetFace] = Array(9).fill("White");
  }
  state.reverifyFace = targetFace;
  state.reverifyColors = [...state.faces[targetFace]];

  reverifyFaceTitle.textContent = `${targetFace}`;
  renderReverifyGrid(reverifyGridEl);

  state.stage = "reverify";
  scanStageSection.classList.remove('active');
  solveStageSection.classList.remove('active');
  reverifyStageSection.classList.add('active');
}

function renderReverifyGrid(container) {
  container.innerHTML = '';
  for (let i = 0; i < 9; i++) {
    const color = state.reverifyColors[i] || "White";

    const cell = document.createElement('div');
    cell.className = 'grid-cell';
    cell.dataset.color = color;
    cell.dataset.index = i;
    cell.textContent = color[0];

    cell.onclick = () => {
      const currentColor = color;
      const nextIndex = (COLOR_NAMES.indexOf(currentColor) + 1) % COLOR_NAMES.length;
      const nextColor = COLOR_NAMES[nextIndex];

      state.reverifyColors[i] = nextColor;
      renderReverifyGrid(container);
    };

    container.appendChild(cell);
  }
}

function handleSaveReverify() {
  const targetFace = state.reverifyFace;
  state.faces[targetFace] = [...state.reverifyColors];

  state.stage = "solve";
  reverifyStageSection.classList.remove('active');
  solveStageSection.classList.add('active');

  solveCube();
}

function handleCancelReverify() {
  state.stage = "solve";
  reverifyStageSection.classList.remove('active');
  solveStageSection.classList.add('active');
}

function switchToSolveStage() {
  stopScanning();
  stopCamera();
  
  state.stage = "solve";
  scanStageSection.classList.remove('active');
  if (reverifyStageSection) reverifyStageSection.classList.remove('active');
  solveStageSection.classList.add('active');
  
  solveCube();
}

function updateProgressUI() {
  const done = Object.keys(state.faces).length;
  progressText.textContent = `${done} / 6`;
  progressFill.style.width = `${(done / 6) * 100}%`;
}

/**
 * Helper to render a small 3x3 color grid for completed faces panel.
 * @param {Array<string>} colors
 * @returns {HTMLElement}
 */
export function renderMiniGrid(colors) {
  const grid = document.createElement('div');
  grid.className = 'mini-grid';
  colors.forEach((color) => {
    const cell = document.createElement('div');
    cell.className = 'mini-cell';
    cell.dataset.color = color;
    grid.appendChild(cell);
  });
  return grid;
}
