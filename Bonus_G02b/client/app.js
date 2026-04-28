const btn = document.getElementById("btn");
const statusEl = document.getElementById("status");
const preview = document.getElementById("preview");

let stream = null;
let canvas = null;
let ctx = null;
let intervalId = null;
let uploadInFlight = false;

function setStatus(message) {
  statusEl.textContent = message;
}

function computeCanvasSize(width, height) {
  const maxWidth = 1280;
  if (!width || !height || width <= maxWidth) {
    return { width, height };
  }

  const scale = maxWidth / width;
  return {
    width: Math.round(width * scale),
    height: Math.round(height * scale),
  };
}

async function start() {
  try {
    stream = await navigator.mediaDevices.getDisplayMedia({ video: true, audio: false });
    preview.srcObject = stream;

    const track = stream.getVideoTracks()[0];
    const settings = track.getSettings();
    const size = computeCanvasSize(settings.width || 1280, settings.height || 720);

    canvas = document.createElement("canvas");
    canvas.width = size.width;
    canvas.height = size.height;
    ctx = canvas.getContext("2d");

    track.addEventListener("ended", stop, { once: true });

    intervalId = window.setInterval(captureAndSend, 1000 / 8);
    btn.textContent = "Stop Sharing Window";
    setStatus(`Sharing ${canvas.width}x${canvas.height} at target 8 FPS`);
  } catch (err) {
    console.error(err);
    stop();
    setStatus("Sharing cancelled or blocked by browser.");
  }
}

function stop() {
  if (intervalId !== null) {
    clearInterval(intervalId);
    intervalId = null;
  }

  uploadInFlight = false;
  if (stream) {
    stream.getTracks().forEach((track) => track.stop());
  }
  stream = null;
  preview.srcObject = null;
  btn.textContent = "Start Sharing Window";
  setStatus("Not sharing");
}

btn.onclick = () => {
  if (intervalId !== null) {
    stop();
    return;
  }
  start();
};

async function captureAndSend() {
  if (!ctx || !canvas || !stream || uploadInFlight) {
    return;
  }

  uploadInFlight = true;
  ctx.drawImage(preview, 0, 0, canvas.width, canvas.height);

  canvas.toBlob(async (blob) => {
    if (!blob) {
      uploadInFlight = false;
      return;
    }

    try {
      const response = await fetch("/upload-frame", {
        method: "POST",
        body: blob,
      });

      if (!response.ok) {
        console.error("Upload failed with status", response.status);
        if (response.status === 413) {
          setStatus("Frame too large for server limit (100000 bytes).");
        } else {
          setStatus(`Upload failed: HTTP ${response.status}`);
        }
      }
    } catch (err) {
      console.error(err);
      setStatus("Upload failed. Stopping sharing.");
      stop();
    } finally {
      uploadInFlight = false;
    }
  }, "image/jpeg", 0.6);
}

setStatus("Not sharing");
