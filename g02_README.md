## Fitur Utama

- Menampilkan halaman web untuk preview webcam.
- Mengganti kamera aktif dari browser.
- Mengambil satu frame JPEG terbaru lewat endpoint HTTP.
- Menyediakan endpoint statistik server.
- Mengirim frame melalui UDP dalam beberapa chunk.
- Menyusun ulang chunk UDP menjadi frame utuh di sisi penerima.
- Menampilkan stream hasil penerimaan UDP menggunakan OpenCV.

## Struktur Folder

```text
g02-webcam-webapp-rivendell/
|-- client/
|   |-- index.html       
|   |-- app.js           
|   `-- udp_receiver.py  
|-- server/
|   |-- http_server.py    
|   |-- udp_sender.py   
|   `-- utils.py       
|-- g02_README.md
|-- README.md
`-- uv.lock
```

## Teknologi yang Digunakan

- **Python** untuk HTTP server, UDP sender, dan UDP receiver.
- **Flask** untuk menyediakan halaman web dan API.
- **OpenCV (`cv2`)** untuk capture webcam, encoding JPEG, dan menampilkan hasil stream UDP.
- **NumPy** untuk membentuk ulang data byte menjadi array gambar saat decoding frame UDP.
- **Requests** untuk mengambil frame dari endpoint HTTP pada sisi sender.
- **HTML, CSS, JavaScript** untuk antarmuka browser.
- **UDP Socket** untuk pengiriman datagram frame.

## Alur Kerja Program

### 1. HTTP Server dan Web UI

File `server/http_server.py` menjalankan Flask server pada port `8000`. Saat browser membuka `/`, server mengirimkan `client/index.html`. File `client/app.js` dilayani melalui endpoint `/app.js`.

Endpoint utama:

| Endpoint | Method | Fungsi |
| --- | --- | --- |
| `/` | GET | Mengirim halaman `index.html`. |
| `/app.js` | GET | Mengirim file JavaScript frontend. |
| `/camera` | POST | Mengganti indeks kamera aktif. |
| `/frame` | GET | Mengambil satu frame terbaru dalam format JPEG. |
| `/stats` | GET | Mengembalikan statistik server dalam format JSON. |

### 2. Pengambilan dan Kompresi Frame

Server membuka kamera aktif menggunakan `cv2.VideoCapture(camera_index)`. Saat endpoint `/frame` dipanggil, server membaca frame terbaru lalu mengompresnya menjadi JPEG memakai `compress_frame()` dari `server/utils.py`.

Selain mengirimkan frame sebagai response `image/jpeg`, server juga memperbarui metrik:

- `frames_served`: total frame yang berhasil dilayani.
- `frame_times`: timestamp 30 frame terakhir.
- `fps`: rata-rata FPS berdasarkan rentang timestamp frame terakhir.

### 3. Preview dan Statistik pada Browser

File `client/app.js` menjalankan dua loop terpisah:

- `updateFrame()` memperbarui elemen `<img>` setiap `125 ms` atau sekitar 8 FPS target.
- `updateStats()` mengambil data dari `/stats` setiap 1 detik.

Statistik yang ditampilkan pada halaman:

- FPS server
- Kamera aktif
- Jumlah frame yang sudah dilayani server

Untuk menghindari cache browser, URL frame diberi query timestamp:

```javascript
previewImg.src = `/frame?t=${new Date().getTime()}`;
```

### 4. Pergantian Kamera

Saat dropdown kamera berubah, browser mengirim `POST /camera` dengan payload:

```json
{
  "camera_index": 0
}
```

Server menggunakan `threading.Lock()` saat mengganti kamera supaya akses terhadap objek `cv2.VideoCapture` tetap aman ketika ada request frame yang berjalan bersamaan.

### 5. Pengiriman Frame Melalui UDP

File `server/udp_sender.py` mengambil data JPEG dari:

```text
http://127.0.0.1:8000/frame
```

Data frame lalu dipecah menjadi beberapa chunk menggunakan `chunk_data()` dari `server/utils.py`, dengan ukuran default `1190` byte per chunk. Setiap chunk diberi header biner sepanjang 10 byte:

```text
[frame_id][chunk_id][total_chunks][payload_len]
```

Header dibentuk dengan:

```python
struct.pack('!IHHH', frame_id, i, total_chunks, len(chunk))
```

Rinciannya:

| Field | Ukuran | Keterangan |
| --- | ---: | --- |
| `frame_id` | 4 byte | ID frame yang sedang dikirim |
| `chunk_id` | 2 byte | Nomor urut chunk |
| `total_chunks` | 2 byte | Total chunk untuk frame tersebut |
| `payload_len` | 2 byte | Panjang payload chunk |

Sender juga mencetak metrik tiap sekitar 1 detik:

- FPS pengiriman perkiraan
- throughput dalam kbps
- jumlah paket UDP yang dikirim

### 6. Penerimaan dan Penyusunan Ulang UDP

File `client/udp_receiver.py` melakukan bind ke `0.0.0.0:5005`, menerima paket hingga 1300 byte, lalu memisahkan 10 byte header dan sisa payload.

Chunk disimpan dalam `frames_buffer` berdasarkan `frame_id`. Jika semua chunk untuk sebuah frame sudah lengkap, receiver:

1. Menyusun payload sesuai urutan `chunk_id`
2. Membentuk `numpy` buffer dari byte hasil gabungan
3. Melakukan decode JPEG dengan `cv2.imdecode`
4. Menampilkan frame melalui `cv2.imshow("UDP Stream", img)`

Receiver juga mencetak statistik periodik:

- `Packets/s`
- `Frames/s`
- total paket dan frame pada interval tersebut

## Cara Menjalankan Program

### 1. Clone Repository

```bash
git clone https://github.com/nafkhanzam-classrooms/g02-webcam-webapp-rivendell.git
cd g02-webcam-webapp-rivendell
```

### 2. Install Dependency

```bash
pip install flask opencv-python numpy requests
```

### 3. Jalankan HTTP Server

```bash
python server/http_server.py
```

Server berjalan pada:

```text
http://127.0.0.1:8000
```

### 4. Jalankan UDP Receiver

```bash
python client/udp_receiver.py
```

Receiver akan menunggu paket UDP pada port `5005`.

### 5. Jalankan UDP Sender

```bash
python server/udp_sender.py
```

Sender akan mengambil frame dari HTTP server, memecah frame menjadi chunk, lalu mengirimkannya ke `127.0.0.1:5005`.