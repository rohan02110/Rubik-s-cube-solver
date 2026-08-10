import { state } from './main.js';
import { renderCube } from './cube3d.js';

/**
 * Sends the scanned face colors to Flask backend, displays progress, and initializes 3D viewer.
 */
export async function solveCube() {
  const container = document.getElementById('cube-container');
  const alertEl = document.getElementById('solution-alert');
  const statusText = document.getElementById('solution-status-text');

  alertEl.className = 'alert alert-info';
  alertEl.textContent = 'Contacting Flask backend to compute optimal solution...';
  statusText.textContent = 'Calculating optimal moves...';

  try {
    const response = await fetch('/api/solve', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ faces: state.faces })
    });

    const result = await response.json();

    if (!response.ok) {
      throw new Error(result.error || "Failed to solve cube");
    }

    // Success
    alertEl.className = 'alert alert-success';
    alertEl.innerHTML = `<strong>Success!</strong> Solution found in <strong>${result.move_count} moves</strong>.`;
    statusText.textContent = `Solution found — ${result.move_count} moves. Use the controls below to walk through each turn.`;

    // Render the 3D cube with the moves
    renderCube(container, state.faces, result.moves);

  } catch (err) {
    // Failure
    alertEl.className = 'alert alert-danger';
    alertEl.innerHTML = `<strong>Cube State Error:</strong> ${err.message}<br><br>` + 
                         `Please select a face below to re-scan it, or check the colors.`;
    statusText.textContent = 'Error solving Rubik\'s cube.';
    
    // Render the static 3D cube (without moves) so the user can inspect it
    renderCube(container, state.faces, []);
  }
}
