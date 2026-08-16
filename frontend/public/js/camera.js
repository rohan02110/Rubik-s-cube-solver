let activeStream = null;

/**
 * Initializes and starts the camera stream on the given video element.
 * @param {HTMLVideoElement} videoEl
 * @returns {Promise<MediaStream>}
 */
export async function startCamera(videoEl) {
  if (activeStream) {
    stopCamera();
  }

  // Ensure mediaDevices API exists
  if (!navigator.mediaDevices) {
    navigator.mediaDevices = {};
  }

  // Polyfill legacy webkit/moz getUserMedia if needed
  if (!navigator.mediaDevices.getUserMedia) {
    const legacyGetUserMedia = navigator.getUserMedia ||
                               navigator.webkitGetUserMedia ||
                               navigator.mozGetUserMedia ||
                               navigator.msGetUserMedia;

    if (legacyGetUserMedia) {
      navigator.mediaDevices.getUserMedia = function (constraints) {
        return new Promise((resolve, reject) => {
          legacyGetUserMedia.call(navigator, constraints, resolve, reject);
        });
      };
    }
  }
  
  if (!navigator.mediaDevices.getUserMedia) {
    const isSecure = window.isSecureContext !== false && (location.hostname === 'localhost' || location.hostname === '127.0.0.1' || location.protocol === 'https:');
    if (!isSecure) {
      throw new Error(`Camera access requires a Secure Context (HTTPS or http://localhost). You are accessing via http://${location.host}. Please access via http://localhost:5000 or http://127.0.0.1:5000.`);
    }
    throw new Error("Camera API (getUserMedia) is not supported by your browser or environment.");
  }
  
  const constraints = {
    video: {
      width: { ideal: 640 },
      height: { ideal: 480 },
      facingMode: "environment" // 'environment' is better for scanning cubes, falls back gracefully
    },
    audio: false
  };

  let stream;
  try {
    stream = await navigator.mediaDevices.getUserMedia(constraints);
  } catch (err) {
    console.warn("Primary camera constraints failed, falling back to any camera:", err);
    stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
  }

  videoEl.srcObject = stream;
  activeStream = stream;
  
  // Make sure the video plays, avoiding race condition if metadata is already loaded
  await new Promise((resolve) => {
    const onReady = () => {
      videoEl.play().catch(e => console.warn("Video play blocked:", e));
      resolve();
    };

    if (videoEl.readyState >= 1) {
      onReady();
    } else {
      videoEl.onloadedmetadata = onReady;
    }
  });
  
  return stream;
}

/**
 * Stops the active camera stream.
 */
export function stopCamera() {
  if (activeStream) {
    activeStream.getTracks().forEach(track => track.stop());
    activeStream = null;
  }
}

/**
 * Captures a JPEG frame from the video element using the offscreen canvas.
 * @param {HTMLVideoElement} videoEl
 * @param {HTMLCanvasElement} canvasEl
 * @returns {Promise<Blob>} JPEG representation of the captured frame
 */
export function captureFrame(videoEl, canvasEl) {
  return new Promise((resolve, reject) => {
    if (!videoEl.videoWidth || !videoEl.videoHeight) {
      reject(new Error("Video not ready"));
      return;
    }

    // Set canvas dimensions matching the video width/height
    canvasEl.width = videoEl.videoWidth;
    canvasEl.height = videoEl.videoHeight;

    const ctx = canvasEl.getContext('2d');
    ctx.drawImage(videoEl, 0, 0, canvasEl.width, canvasEl.height);

    canvasEl.toBlob((blob) => {
      if (blob) {
        resolve(blob);
      } else {
        reject(new Error("Canvas blob conversion failed"));
      }
    }, 'image/jpeg', 0.85); // JPEG compression at 85% quality
  });
}
