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
  stage: "scan", // "scan" | "solve"
  faces: {}, // Stores locked colors for each face key, e.g. { "F": [...] }
  currentFaceIndex: 0,
  corrections: {}, // Manual user corrections per face: { "F": { 0: "Yellow" } }
  liveDetected: Array(9).fill("White"), // Live frame sample classifications
  liveHsv: Array(9).fill([0, 0, 0]), // Live frame raw HSV values
  snapshotColors: Array(9).fill("White"), // Snapshot of colors copied for verification
  legend: null, // Custom HSV color centers mapping
  calibrationStep: 0, // Current index of color being calibrated
  isCalibrated: false // Flag indicating if custom calibration is active
};

// DOM Cache
let videoEl, canvasEl, overlayCanvasEl, gridContainerEl, lockBtn, resetBtn, scanStageSection, solveStageSection;
let progressText, progressFill, faceHeader, instructionBox, scanTriggerBtn;
let rescanSelect, rescanSingleBtn, scanAllBtn, completedList, completedSection;

// Calibration DOM Cache
let legendPanel, calibrationGuide, captureLegendBtn, skipLegendBtn, recalibrateLegendBtn;
let scanningHeaderContainer, scanningActions, calibrationActions;

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

  // Calibration DOM Cache init
  legendPanel = document.getElementById('legend-panel');
  calibrationGuide = document.getElementById('calibration-guide');
  captureLegendBtn = document.getElementById('capture-legend-btn');
  skipLegendBtn = document.getElementById('skip-legend-btn');
  recalibrateLegendBtn = document.getElementById('recalibrate-legend-btn');
  scanningHeaderContainer = document.getElementById('scanning-header-container');
  scanningActions = document.getElementById('scanning-actions');
  calibrationActions = document.getElementById('calibration-actions');

  // Event Handlers Setup
  lockBtn.onclick = handleLockFace;
  resetBtn.onclick = handleResetScan;
  scanAllBtn.onclick = handleResetScan;
  rescanSingleBtn.onclick = handleRescanSingleFace;
  scanTriggerBtn.onclick = handleScanTrigger;

  // Calibration Event Handlers
  captureLegendBtn.onclick = handleCaptureLegendColor;
  skipLegendBtn.onclick = handleSkipCalibration;
  recalibrateLegendBtn.onclick = handleRecalibrateLegend;

  // Initialize UI
  updateProgressUI();
  await initScanStage();
});

export async function initScanStage() {
  state.stage = "scan";
  solveStageSection.classList.remove('active');
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

  // Update Stage Visibility based on calibration state
  updateStageVisibility();

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

// Calibration UI visibility helper
function updateStageVisibility() {
  if (state.isCalibrated) {
    // Show scanning UI
    scanningHeaderContainer.style.display = "block";
    scanningActions.style.display = "block";
    calibrationActions.style.display = "none";
    calibrationGuide.style.display = "none";
    recalibrateLegendBtn.style.display = "inline-block";
    legendPanel.classList.add("complete");
  } else {
    // Show calibration UI
    scanningHeaderContainer.style.display = "none";
    scanningActions.style.display = "none";
    calibrationActions.style.display = "block";
    calibrationGuide.style.display = "block";
    recalibrateLegendBtn.style.display = "none";
    legendPanel.classList.remove("complete");
    updateCalibrationSwatchesUI();
  }
}

// Update the visual state of the swatches
function updateCalibrationSwatchesUI() {
  COLOR_NAMES.forEach((color, idx) => {
    const swatch = document.getElementById(`swatch-${color}`);
    if (!swatch) return;

    swatch.classList.remove("active");
    
    const statusSpan = swatch.querySelector(".swatch-status");
    const previewDiv = swatch.querySelector(".swatch-color");

    if (state.legend && state.legend[color]) {
      // Swatch is calibrated
      swatch.classList.add("complete");
      statusSpan.textContent = "Ready";
      // Render preview of HSV color if stored
      if (swatch.dataset.rgb) {
        previewDiv.style.backgroundColor = swatch.dataset.rgb;
      }
    } else {
      swatch.classList.remove("complete");
      statusSpan.textContent = "Pending";
      // Restore standard CSS var colors
      previewDiv.style.backgroundColor = `var(--sticker-${color})`;
    }

    if (idx === state.calibrationStep && !state.isCalibrated) {
      swatch.classList.add("active");
      statusSpan.textContent = "Capture";
      calibrationGuide.innerHTML = `Place the <strong>${color}</strong> center sticker in the center box of the camera, then click "Capture Reference Color".`;
    }
  });
}

function handleCaptureLegendColor() {
  if (state.isCalibrated) return;

  const currentColor = COLOR_NAMES[state.calibrationStep];
  
  // Ensure we have a valid HSV sample
  if (!state.liveHsv || state.liveHsv.length !== 9) {
    console.warn("Live HSV frame data not ready yet.");
    return;
  }

  // Raw HSV of the center cell (index 4)
  const centerHsv = state.liveHsv[4];
  
  if (!state.legend) {
    state.legend = {};
  }
  state.legend[currentColor] = centerHsv;

  // Sample actual center pixel RGB from canvas for high accuracy visual preview
  let rgbColor = `var(--sticker-${currentColor})`;
  try {
    const ctx = canvasEl.getContext('2d');
    const w = canvasEl.width;
    const h = canvasEl.height;
    if (w && h) {
      const size = Math.min(w, h);
      const cx = (w - size) / 2 + size / 2;
      const cy = (h - size) / 2 + size / 2;
      // Get 10x10 block around center
      const imgData = ctx.getImageData(cx - 5, cy - 5, 10, 10);
      let r = 0, g = 0, b = 0;
      const count = imgData.data.length / 4;
      for (let i = 0; i < imgData.data.length; i += 4) {
        r += imgData.data[i];
        g += imgData.data[i+1];
        b += imgData.data[i+2];
      }
      r = Math.round(r / count);
      g = Math.round(g / count);
      b = Math.round(b / count);
      rgbColor = `rgb(${r}, ${g}, ${b})`;
    }
  } catch (err) {
    console.warn("Failed to sample preview color:", err);
  }

  const swatch = document.getElementById(`swatch-${currentColor}`);
  if (swatch) {
    swatch.dataset.rgb = rgbColor;
  }

  // Advance calibration step
  state.calibrationStep++;
  if (state.calibrationStep >= COLOR_NAMES.length) {
    state.isCalibrated = true;
  }

  updateStageVisibility();
}

function handleSkipCalibration() {
  state.legend = null;
  state.isCalibrated = true;
  updateStageVisibility();
}

function handleRecalibrateLegend() {
  state.legend = null;
  state.calibrationStep = 0;
  state.isCalibrated = false;
  
  // Clear swatch RGBs
  COLOR_NAMES.forEach(color => {
    const swatch = document.getElementById(`swatch-${color}`);
    if (swatch) {
      delete swatch.dataset.rgb;
    }
  });

  updateStageVisibility();
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

function switchToSolveStage() {
  stopScanning();
  stopCamera();
  
  state.stage = "solve";
  scanStageSection.classList.remove('active');
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
