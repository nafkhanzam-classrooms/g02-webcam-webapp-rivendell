# Laporan Program: Browser Window Mirror dengan HTTP dan UDP Broadcast

## 1. Deskripsi Singkat

Program ini adalah aplikasi sederhana untuk melakukan **mirroring tampilan window/browser** dari sisi pengirim ke sisi penerima melalui jaringan lokal. Aplikasi bekerja dengan menangkap tampilan layar atau window dari browser, mengirim frame hasil tangkapan ke server HTTP, lalu meneruskan frame tersebut melalui UDP broadcast agar dapat diterima dan ditampilkan oleh komputer lain di jaringan yang sama.

Secara umum, sistem terdiri dari empat bagian utama:

1. **Client browser**
   - `index.html`
   - `app.js`

2. **HTTP server**
   - `http_server.py`

3. **UDP sender**
   - `udp_sender.py`

4. **UDP receiver**
   - `udp_receiver.py`

Alur kerja program:

```text
Browser Teacher
      |
      | POST /upload-frame
      v
HTTP Server
      |
      | GET /frame
      v
UDP Sender
      |
      | UDP Broadcast
      v
UDP Receiver
      |
      v
OpenCV Display Window
```

---

## 2. Tujuan Program

Tujuan utama program ini adalah membuat sistem berbagi tampilan layar sederhana menggunakan kombinasi:

- **Web browser** untuk menangkap tampilan layar atau window.
- **HTTP server** untuk menerima dan menyimpan frame terbaru.
- **UDP broadcast** untuk menyebarkan frame ke perangkat lain dalam satu jaringan lokal.
- **OpenCV** untuk menampilkan frame hasil penerimaan di sisi receiver.

Program ini dapat digunakan sebagai contoh implementasi konsep:

- Screen sharing sederhana.
- Komunikasi HTTP client-server.
- Pengiriman data menggunakan UDP.
- Fragmentasi data menjadi beberapa paket UDP.
- Rekonstruksi data dari paket-paket UDP.
- Pemrosesan citra menggunakan OpenCV.

---

## 3. Struktur File

```text
project/
├── client/
│   ├── index.html
│   └── app.js
├── server/
│   ├── http_server.py
│   ├── udp_sender.py
│   └── udp_receiver.py
└── README.md
```

Keterangan:

| File | Fungsi |
|---|---|
| `index.html` | Halaman web utama untuk teacher dashboard. |
| `app.js` | Script browser untuk menangkap window/screen dan mengirim frame ke server. |
| `http_server.py` | Server HTTP untuk menerima frame dari browser dan menyediakan frame terbaru. |
| `udp_sender.py` | Mengambil frame dari HTTP server, memecahnya menjadi paket UDP, lalu melakukan broadcast. |
| `udp_receiver.py` | Menerima paket UDP, menyusun ulang frame JPEG, lalu menampilkannya dengan OpenCV. |

---

## 4. Penjelasan Setiap File

## 4.1 `index.html`

File `index.html` adalah halaman web sederhana yang digunakan oleh pengguna sisi pengirim, misalnya guru atau presenter.

Elemen utama pada file ini adalah:

```html
<button id="btn">Start Sharing Window</button>
<p id="status"></p>
<video id="preview" autoplay muted playsinline></video>
```

Fungsi masing-masing elemen:

- Tombol `Start Sharing Window` digunakan untuk memulai atau menghentikan proses screen sharing.
- Elemen `status` digunakan untuk menampilkan kondisi aplikasi, misalnya sedang berbagi layar atau tidak.
- Elemen `video` digunakan untuk menampilkan preview tampilan layar/window yang sedang dibagikan.

File ini juga memuat script:

```html
<script src="/app.js"></script>
```

Script tersebut berisi logika utama untuk menangkap tampilan layar dari browser.

---

## 4.2 `app.js`

File `app.js` menjalankan proses capture tampilan layar dari browser menggunakan API:

```javascript
navigator.mediaDevices.getDisplayMedia({ video: true, audio: false })
```

API tersebut meminta izin pengguna untuk memilih layar, window, atau tab browser yang ingin dibagikan.

### Fungsi penting dalam `app.js`

### a. `setStatus(message)`

```javascript
function setStatus(message) {
  statusEl.textContent = message;
}
```

Fungsi ini digunakan untuk mengubah teks status pada halaman web.

### b. `computeCanvasSize(width, height)`

```javascript
function computeCanvasSize(width, height) {
  const maxWidth = 1280;
  ...
}
```

Fungsi ini membatasi lebar maksimum frame menjadi `1280` piksel. Jika resolusi sumber lebih besar, ukuran frame akan diperkecil secara proporsional.

Tujuannya adalah:

- Mengurangi ukuran data frame.
- Mengurangi beban jaringan.
- Membantu agar ukuran JPEG tidak melebihi batas server.

### c. `start()`

Fungsi `start()` bertugas untuk:

1. Meminta akses screen/window sharing dari browser.
2. Menampilkan stream ke elemen video preview.
3. Membuat elemen canvas.
4. Mengambil ukuran video dari track yang dipilih.
5. Menjalankan pengambilan frame secara periodik.

Interval pengiriman frame diatur dengan:

```javascript
intervalId = window.setInterval(captureAndSend, 1000 / 8);
```

Artinya target frame rate adalah sekitar **8 FPS**.

### d. `stop()`

Fungsi `stop()` menghentikan proses sharing dengan cara:

- Menghapus interval capture.
- Menghentikan semua media track.
- Menghapus preview dari elemen video.
- Mengubah teks tombol kembali menjadi `Start Sharing Window`.
- Mengatur status menjadi `Not sharing`.

### e. `captureAndSend()`

Fungsi ini adalah inti dari proses pengiriman frame dari browser ke server.

Langkah kerjanya:

1. Menggambar frame video ke canvas.
2. Mengubah canvas menjadi blob JPEG.
3. Mengirim blob tersebut ke endpoint HTTP:

```javascript
fetch("/upload-frame", {
  method: "POST",
  body: blob,
});
```

Format gambar yang dikirim adalah:

```javascript
"image/jpeg", 0.6
```

Artinya frame dikompresi sebagai JPEG dengan kualitas `0.6`.

Variabel `uploadInFlight` digunakan agar browser tidak mengirim frame baru ketika frame sebelumnya masih dalam proses upload. Ini mencegah penumpukan request.

---

## 4.3 `http_server.py`

File `http_server.py` adalah HTTP server berbasis Python yang menggunakan:

```python
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
```

Server berjalan pada port:

```python
PORT = 8000
```

Server ini memiliki beberapa endpoint:

| Endpoint | Method | Fungsi |
|---|---|---|
| `/` | GET | Mengirim halaman `index.html`. |
| `/app.js` | GET | Mengirim file JavaScript client. |
| `/upload-frame` | POST | Menerima frame JPEG dari browser. |
| `/frame` | GET | Mengirim frame JPEG terbaru. |
| `/stats` | GET | Mengirim statistik dalam format JSON. |

### Batas ukuran frame

Server membatasi ukuran frame maksimum:

```python
MAX_FRAME_SIZE = 100_000
```

Artinya frame yang dikirim browser tidak boleh lebih dari **100.000 byte**. Jika lebih besar, server akan merespons dengan status:

```text
413 Frame too large
```

### Penyimpanan state

Server menyimpan state frame terbaru dalam dictionary:

```python
_state = {
    "latest_frame": b"",
    "frame_id": 0,
    "frames_uploaded": 0,
    "frames_served": 0,
    "upload_times": [],
}
```

Keterangan:

- `latest_frame`: menyimpan frame JPEG terbaru.
- `frame_id`: nomor urut frame.
- `frames_uploaded`: jumlah frame yang berhasil di-upload.
- `frames_served`: jumlah frame yang pernah diambil melalui endpoint `/frame`.
- `upload_times`: daftar timestamp upload untuk menghitung FPS.

Akses ke `_state` dilindungi menggunakan:

```python
_lock = threading.Lock()
```

Tujuannya agar aman ketika ada banyak request HTTP yang berjalan secara paralel.

---

## 4.4 `udp_sender.py`

File `udp_sender.py` bertugas mengambil frame terbaru dari HTTP server, lalu mengirimkannya melalui UDP broadcast.

Frame diambil dari:

```python
FRAME_URL = "http://127.0.0.1:8000/frame"
```

Tujuan broadcast UDP:

```python
DEST_IP = "255.255.255.255"
DEST_PORT = 5000
```

Target frame rate:

```python
TARGET_FPS = 8
```

### Format paket UDP

Frame JPEG biasanya lebih besar dari ukuran aman satu paket UDP. Karena itu, frame harus dipecah menjadi beberapa chunk.

Format header paket:

```text
[frame_id:4][chunk_id:2][total_chunks:2][payload_len:2][payload]
```

Header dikodekan menggunakan format struct:

```python
HEADER_FMT = "!IHHH"
```

Makna field:

| Field | Ukuran | Keterangan |
|---|---:|---|
| `frame_id` | 4 byte | ID unik untuk setiap frame. |
| `chunk_id` | 2 byte | Nomor urut chunk dalam frame. |
| `total_chunks` | 2 byte | Jumlah total chunk untuk frame tersebut. |
| `payload_len` | 2 byte | Panjang data payload dalam paket. |

Ukuran maksimum paket:

```python
MTU = 1200
```

Karena header berukuran 10 byte, maka payload maksimum per paket adalah:

```python
chunk_payload = MTU - HEADER_LEN
```

### Pencegahan pengiriman frame duplikat

Program menggunakan hash:

```python
digest = blake2b(frame, digest_size=8).digest()
```

Jika hash frame sama dengan frame sebelumnya, maka frame tidak dikirim ulang. Ini mengurangi penggunaan bandwidth ketika tampilan layar tidak berubah.

### Statistik pengiriman

Program mencetak statistik berupa:

- FPS terkirim.
- Jumlah paket per detik.
- Throughput dalam kbps.

Contoh format output:

```text
[UDP sender] fps=8.00 packets/s=120.00 throughput=950.00 kbps
```

---

## 4.5 `udp_receiver.py`

File `udp_receiver.py` bertugas menerima paket UDP broadcast pada port:

```python
PORT = 5000
```

Receiver menggunakan socket UDP:

```python
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(("", PORT))
```

Artinya receiver menerima paket dari semua interface jaringan pada port `5000`.

### Proses penerimaan paket

Setiap paket UDP dibaca dengan:

```python
pkt, _ = sock.recvfrom(1500)
```

Kemudian header dipisahkan dari payload:

```python
frame_id, chunk_id, total_chunks, payload_len = struct.unpack(
    HEADER_FMT, pkt[:HEADER_LEN]
)
payload = pkt[HEADER_LEN:HEADER_LEN + payload_len]
```

### Rekonstruksi frame

Setiap frame disimpan sementara berdasarkan `frame_id`:

```python
frames = {}
```

Jika semua chunk dari satu frame sudah diterima, maka frame dirakit ulang:

```python
jpeg = b"".join(meta["arrived"][i] for i in range(meta["total_chunks"]))
```

Setelah itu, JPEG didekode menjadi gambar OpenCV:

```python
img = cv2.imdecode(np.frombuffer(jpeg, np.uint8), cv2.IMREAD_COLOR)
```

Gambar ditampilkan menggunakan:

```python
cv2.imshow("Mirrored Window", img)
cv2.waitKey(1)
```

### Timeout frame

Jika frame tidak lengkap dalam waktu:

```python
TIMEOUT = 2.0
```

maka frame tersebut dihapus dari buffer. Hal ini penting karena UDP tidak menjamin semua paket sampai ke tujuan.

---

## 5. Alur Kerja Program

Berikut adalah alur kerja lengkap program:

1. User membuka halaman web dari HTTP server.
2. User menekan tombol `Start Sharing Window`.
3. Browser meminta izin memilih layar/window/tab yang akan dibagikan.
4. Browser menampilkan preview pada elemen video.
5. JavaScript mengambil frame dari video preview ke canvas.
6. Canvas dikonversi menjadi JPEG.
7. JPEG dikirim ke HTTP server melalui `POST /upload-frame`.
8. HTTP server menyimpan frame terbaru di memory.
9. UDP sender mengambil frame dari `GET /frame`.
10. UDP sender memecah frame menjadi beberapa paket UDP.
11. Paket UDP dikirim ke alamat broadcast `255.255.255.255:5000`.
12. UDP receiver menerima paket-paket tersebut.
13. UDP receiver menyusun ulang chunk menjadi JPEG.
14. JPEG didekode menjadi gambar.
15. Gambar ditampilkan menggunakan OpenCV.

---

## 6. Cara Menjalankan Program

## 6.1 Persiapan Dependency

Pastikan Python sudah terpasang. Kemudian install dependency berikut:

```bash
pip install requests opencv-python numpy
```

Browser yang digunakan harus mendukung API `getDisplayMedia`, misalnya:

- Google Chrome
- Microsoft Edge
- Firefox versi modern

---

## 6.2 Menjalankan HTTP Server

Jalankan file:

```bash
python http_server.py
```

Jika berhasil, akan muncul output:

```text
HTTP server listening on http://127.0.0.1:8000
```

Buka browser ke alamat:

```text
http://127.0.0.1:8000
```

---

## 6.3 Menjalankan UDP Sender

Pada terminal lain, jalankan:

```bash
python udp_sender.py
```

Program ini akan mengambil frame terbaru dari HTTP server dan mengirimkannya melalui UDP broadcast.

---

## 6.4 Menjalankan UDP Receiver

Pada perangkat penerima yang berada dalam jaringan lokal yang sama, jalankan:

```bash
python udp_receiver.py
```

Jika paket UDP berhasil diterima dan frame berhasil disusun, akan muncul window OpenCV dengan judul:

```text
Mirrored Window
```

---

## 6.5 Memulai Sharing

Pada halaman browser:

1. Tekan tombol `Start Sharing Window`.
2. Pilih window, tab, atau layar yang ingin dibagikan.
3. Browser akan menampilkan preview.
4. Receiver akan mulai menampilkan hasil mirroring.

Untuk berhenti, tekan tombol:

```text
Stop Sharing Window
```

---

## 7. Protokol Komunikasi

Program menggunakan dua jenis komunikasi:

## 7.1 HTTP

HTTP digunakan antara browser dan server, serta antara UDP sender dan server.

| Komunikasi | Protokol | Endpoint |
|---|---|---|
| Browser ke server | HTTP POST | `/upload-frame` |
| UDP sender ke server | HTTP GET | `/frame` |
| Browser mengambil halaman | HTTP GET | `/` |
| Browser mengambil JS | HTTP GET | `/app.js` |
| Monitoring statistik | HTTP GET | `/stats` |

HTTP dipilih karena mudah digunakan oleh browser dan cocok untuk komunikasi antara client web dan server lokal.

---

## 7.2 UDP Broadcast

UDP digunakan untuk menyebarkan frame ke receiver.

Keuntungan UDP:

- Latency rendah.
- Tidak membutuhkan koneksi permanen.
- Cocok untuk data real-time seperti frame video.
- Bisa dikirim ke banyak receiver melalui broadcast.

Kekurangan UDP:

- Paket bisa hilang.
- Paket bisa datang tidak berurutan.
- Tidak ada mekanisme retransmission otomatis.
- Frame dapat gagal ditampilkan jika ada chunk yang hilang.

Karena itu, program menggunakan `frame_id`, `chunk_id`, dan `total_chunks` agar receiver bisa menyusun ulang frame yang terpecah.

---
## Screenshot Hasil

<img width="2560" height="1600" alt="image" src="https://github.com/user-attachments/assets/58b1ff53-15a2-41b1-be53-7df240390b51" />

<img width="2035" height="549" alt="image" src="https://github.com/user-attachments/assets/287633a8-e2cd-4b97-98a4-55070fd23427" />



## Kesimpulan

Program ini merupakan implementasi sederhana dari sistem mirroring tampilan layar menggunakan kombinasi HTTP dan UDP broadcast. Browser bertugas menangkap tampilan layar dan mengirim frame ke HTTP server. Server menyimpan frame terbaru. UDP sender mengambil frame dari server dan mengirimkannya dalam bentuk paket-paket UDP broadcast. UDP receiver menerima paket, menyusun ulang frame, lalu menampilkannya menggunakan OpenCV.

Dari sisi pembelajaran, program ini baik untuk memahami konsep jaringan komputer, khususnya perbedaan karakteristik HTTP dan UDP. HTTP digunakan untuk komunikasi yang lebih terstruktur antara browser dan server, sedangkan UDP digunakan untuk pengiriman real-time dengan latency rendah. Namun, karena UDP tidak menjamin keandalan pengiriman, program perlu menangani fragmentasi, rekonstruksi, dan timeout frame.

Secara keseluruhan, program sudah mampu menunjukkan prinsip dasar screen mirroring sederhana pada jaringan lokal, tetapi masih dapat dikembangkan lebih lanjut pada aspek keamanan, reliability, konfigurasi, dan efisiensi bandwidth.
