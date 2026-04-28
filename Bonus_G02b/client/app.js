const btn     = document.getElementById("btn");
const recBtn  = document.createElement("button");  // tombol rekam
recBtn.textContent = "Start Recording";
document.body.insertBefore(recBtn, btn.nextSibling);
const preview = document.getElementById("preview");
let stream, canvas, ctx, intervalID;
let recorder, chunks = [];


async function start() {
  stream = await navigator.mediaDevices.getDisplayMedia({video: true});
  preview.srcObject = stream;

  canvas = document.createElement("canvas");
  canvas.width  = stream.getVideoTracks()[0].getSettings().width;
  canvas.height = stream.getVideoTracks()[0].getSettings().height;
  ctx = canvas.getContext("2d");

  intervalID = setInterval(captureAndSend, 1000/8); // 8 FPS
  btn.textContent = "Stop Sharing";

  recBtn.disabled  = false;           // baru boleh merekam kalau sudah share

  // --- siapkan MediaRecorder --------------------------------------------
  recorder = new MediaRecorder(stream, {mimeType:"video/webm"});
  recorder.ondataavailable = e => chunks.push(e.data);
  recorder.onstop = () => {
      const blob = new Blob(chunks, {type:"video/webm"});
      const url  = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `recording-${Date.now()}.webm`;
      a.click();
      chunks = [];
  };
}
function stop() {
  clearInterval(intervalID);
  stream.getTracks().forEach(t => t.stop());
  btn.textContent = "Start Sharing Window";
  recBtn.textContent = "Start Recording";
  recBtn.disabled = true;
  if (recorder?.state === "recording") recorder.stop();
}

btn.onclick = () => (intervalID ? stop() : start());
recBtn.onclick = () => {
    if (recorder.state === "inactive"){
        recorder.start();
        recBtn.textContent = "Stop Recording";
    }else{
        recorder.stop();
    }
};
recBtn.disabled = true;

async function captureAndSend() {
  ctx.drawImage(preview, 0, 0, canvas.width, canvas.height);
  canvas.toBlob(async blob => {
    if (!blob) return;
    try {
      await fetch("/upload-frame", {method:"POST", body:blob});
    } catch(err) {
      console.error(err);
      stop();
    }
  }, "image/jpeg", 0.75);
}