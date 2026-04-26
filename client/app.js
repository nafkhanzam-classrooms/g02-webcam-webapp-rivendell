const cameraSelect = document.getElementById('cameraSelect');
const previewImg = document.getElementById('preview');
const statsDiv = document.getElementById('stats');

cameraSelect.addEventListener('change', async () => {
    const idx = cameraSelect.value;
    try {
        const response = await fetch('/camera', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ camera_index: parseInt(idx) })
        });
        const result = await response.json();
        console.log("Camera switched to:", result.camera_index);
    } catch (err) {
        alert("Failed to switch camera");
    }
});

async function updateFrame() {
    previewImg.src = `/frame?t=${new Date().getTime()}`;
    
    setTimeout(updateFrame, 125); 
}

updateFrame();