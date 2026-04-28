# Network Programming - Assignment G02
## Anggota Kelompok

| Nama           | NRP        | Kelas     |
| ---            | ---        | ----------|
| Justin Valentino | 5025241234 | C   |
|  Farrel Jatmiko Aji | 5025241193  | C  |

## Link Youtube (Unlisted)
```

```

## Penjelasan Program
Program ini dibuat untuk memenuhi tugas **Network Programming - Assignment G02**. Secara umum, aplikasi bekerja dengan mengambil gambar dari webcam menggunakan OpenCV, mengompres frame menjadi format JPEG, lalu menampilkannya melalui halaman web. Selain itu, program juga menyediakan mekanisme pengiriman frame melalui UDP dengan cara memecah data gambar menjadi beberapa potongan kecil atau *chunks* agar dapat dikirim melalui datagram UDP.

Fitur utama program:

- Menampilkan halaman web kontrol webcam.
- Mengambil frame dari webcam menggunakan OpenCV.
- Mengompres frame menjadi JPEG.
- Menyediakan endpoint HTTP untuk mengambil frame terbaru.
- Mengganti kamera melalui pilihan pada halaman web.
- Mengirim frame melalui UDP dalam bentuk potongan data.
- Menerima dan menyusun ulang frame UDP di sisi client.

## Struktur Folder

```text
g02-webcam-webapp-rivendell/
├── client/
│   ├── index.html        # Halaman web utama untuk kontrol dan preview webcam
│   ├── app.js            # Script frontend untuk update frame dan pemilihan kamera
│   └── udp_receiver.py   # Program penerima frame melalui UDP
├── server/
│   ├── http_server.py    # Flask server untuk halaman web, endpoint kamera, dan endpoint frame
│   ├── udp_sender.py     # Program pengirim frame melalui UDP
│   └── utils.py          # Fungsi utilitas untuk kompresi frame dan pemecahan data
├── README.md
├── uv.lock
└── .gitignore
```

## Teknologi yang Digunakan

- **Python**: bahasa utama untuk server, pengiriman UDP, dan penerimaan UDP.
- **Flask**: framework HTTP server untuk menyediakan halaman web dan endpoint API.
- **OpenCV (`cv2`)**: digunakan untuk membaca webcam dan melakukan encoding frame ke JPEG.
- **NumPy**: digunakan pada receiver untuk mengubah byte hasil UDP menjadi array sebelum didekode oleh OpenCV.
- **Requests**: digunakan oleh UDP sender untuk mengambil frame dari endpoint HTTP.
- **HTML, CSS, JavaScript**: digunakan untuk membangun antarmuka web.
- **UDP Socket**: digunakan untuk mengirim dan menerima frame sebagai datagram.

## Alur Kerja Program

### 1. HTTP Server Menyediakan Halaman Web

File `server/http_server.py` menjalankan Flask server pada port `8000`. Ketika pengguna membuka halaman utama, server mengirimkan file `client/index.html`. File JavaScript `client/app.js` juga dilayani oleh server melalui endpoint `/app.js`.

Endpoint utama:

| Endpoint | Method | Fungsi |
|---|---|---|
| `/` | GET | Mengirim halaman `index.html` ke browser. |
| `/app.js` | GET | Mengirim file JavaScript frontend. |
| `/camera` | POST | Mengganti indeks kamera yang digunakan. |
| `/frame` | GET | Mengambil satu frame terbaru dari webcam dalam format JPEG. |

### 2. Pengambilan Frame dari Webcam

Pada awal program, `http_server.py` membuka kamera default dengan:

```python
cap = cv2.VideoCapture(camera_index)
```

Nilai awal `camera_index` adalah `0`, sehingga kamera default sistem akan digunakan. Ketika endpoint `/frame` dipanggil, server membaca frame dari webcam menggunakan:

```python
success, frame = cap.read()
```

Jika pembacaan berhasil, frame dikompres menjadi JPEG menggunakan fungsi `compress_frame()` dari `server/utils.py`, lalu dikirim sebagai response HTTP dengan MIME type `image/jpeg`.

### 3. Tampilan Web Client

File `client/index.html` berisi halaman sederhana dengan elemen berikut:

- Judul panel kontrol webcam.
- Dropdown untuk memilih kamera.
- Elemen `<img>` untuk menampilkan preview frame.
- Elemen status untuk informasi FPS dan status aplikasi.

File `client/app.js` bertugas melakukan dua pekerjaan utama:

1. Mengirim request `POST /camera` ketika pengguna memilih kamera lain dari dropdown.
2. Memperbarui gambar webcam secara periodik dengan mengganti `src` elemen `<img>` ke endpoint `/frame`.

Frame diperbarui setiap `125 ms`, sehingga target tampilan di browser adalah sekitar:

```text
1000 ms / 125 ms = 8 FPS
```

Untuk menghindari browser menggunakan cache gambar lama, URL frame diberi parameter waktu:

```javascript
previewImg.src = `/frame?t=${new Date().getTime()}`;
```

### 4. Pergantian Kamera

Ketika pengguna memilih kamera dari dropdown, JavaScript mengirim data JSON ke endpoint `/camera`:

```json
{
  "camera_index": 0
}
```

Server kemudian:

1. Membaca indeks kamera baru.
2. Mengunci proses dengan `threading.Lock()` agar akses kamera aman.
3. Melepas kamera lama dengan `cap.release()`.
4. Membuka kamera baru dengan `cv2.VideoCapture(camera_index)`.
5. Mengirim response JSON berisi status dan indeks kamera aktif.

### 5. Pengiriman Frame Melalui UDP

File `server/udp_sender.py` mengambil frame dari endpoint HTTP:

```text
http://127.0.0.1:8000/frame
```

Setelah frame JPEG diperoleh, data frame dipecah menjadi beberapa potongan menggunakan fungsi `chunk_data()` dari `server/utils.py`. Ukuran default setiap chunk adalah `1190` byte.

Setiap chunk dikirim sebagai paket UDP dengan format:

```text
[header 10 byte][payload]
```

Header dibuat menggunakan `struct.pack('!IHHH', frame_id, i, total_chunks, len(chunk))`.

Format header:

| Field | Ukuran | Tipe | Keterangan |
|---|---:|---|---|
| `frame_id` | 4 byte | Unsigned int | ID unik untuk setiap frame. |
| `chunk_id` | 2 byte | Unsigned short | Nomor urut chunk dalam satu frame. |
| `total_chunks` | 2 byte | Unsigned short | Jumlah total chunk untuk frame tersebut. |
| `payload_len` | 2 byte | Unsigned short | Panjang payload pada chunk. |

Karena header berukuran 10 byte dan payload default 1190 byte, ukuran paket UDP menjadi sekitar 1200 byte. Nilai ini menjaga ukuran datagram tetap relatif kecil agar lebih aman terhadap fragmentasi jaringan.

UDP sender memiliki target pengiriman sekitar 8 FPS dengan jeda:

```python
time.sleep(1/8)
```

### 6. Penerimaan Frame Melalui UDP

File `client/udp_receiver.py` membuat socket UDP pada alamat:

```text
0.0.0.0:5005
```

Program menerima paket UDP dengan ukuran buffer `1300` byte. Setiap paket dipisahkan menjadi header dan payload:

```python
header = packet[:10]
payload = packet[10:]
```

Header dibaca kembali menggunakan:

```python
frame_id, chunk_id, total_chunks, payload_len = struct.unpack('!IHHH', header)
```

Potongan frame disimpan dalam dictionary `frames_buffer`. Ketika seluruh chunk untuk satu `frame_id` sudah diterima, program menyusun ulang data frame dengan urutan `chunk_id`, lalu melakukan decode JPEG menggunakan OpenCV:

```python
img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
```

Jika decode berhasil, frame ditampilkan menggunakan:

```python
cv2.imshow("UDP Stream", img)
```

Program receiver dapat dihentikan dengan menekan tombol `q` pada jendela OpenCV.

## Cara Menjalankan Program

### 1. Clone Repository

```bash
git clone https://github.com/nafkhanzam-classrooms/g02-webcam-webapp-rivendell.git
cd g02-webcam-webapp-rivendell
```

### 2. Install Dependency

Pastikan Python sudah terpasang. Kemudian install dependency yang dibutuhkan:

```bash
pip install flask opencv-python numpy requests
```

### 3. Jalankan HTTP Server

Jalankan server Flask dari folder `server`:

```bash
cd server
python http_server.py
```

Server akan berjalan pada:

```text
http://127.0.0.1:8000
```

Buka alamat tersebut melalui browser untuk melihat halaman kontrol webcam.

### 4. Jalankan UDP Receiver

Buka terminal baru dari root repository, lalu jalankan:

```bash
python client/udp_receiver.py
```

Receiver akan menunggu paket UDP pada port `5005`.

### 5. Jalankan UDP Sender

Buka terminal lain, masuk ke folder `server`, lalu jalankan:

```bash
cd server
python udp_sender.py
```

UDP sender akan mengambil frame dari HTTP server, memecah frame menjadi beberapa chunk, lalu mengirimkannya ke receiver UDP pada `127.0.0.1:5005`.

## Konfigurasi Penting

Beberapa konfigurasi yang dapat diubah:

| File | Variabel | Nilai Default | Fungsi |
|---|---|---:|---|
| `server/http_server.py` | `camera_index` | `0` | Menentukan kamera default. |
| `server/http_server.py` | `app.run(port=8000)` | `8000` | Menentukan port HTTP server. |
| `server/udp_sender.py` | `UDP_IP` | `127.0.0.1` | Alamat tujuan pengiriman UDP. |
| `server/udp_sender.py` | `UDP_PORT` | `5005` | Port tujuan UDP. |
| `server/udp_sender.py` | `HTTP_URL` | `http://127.0.0.1:8000/frame` | Endpoint sumber frame. |
| `server/utils.py` | `quality` | `50` | Kualitas kompresi JPEG. |
| `server/utils.py` | `chunk_size` | `1190` | Ukuran payload setiap paket UDP. |
| `client/udp_receiver.py` | `UDP_IP` | `0.0.0.0` | Alamat bind receiver UDP. |
| `client/udp_receiver.py` | `UDP_PORT` | `5005` | Port receiver UDP. |

Jika sender dan receiver dijalankan pada perangkat berbeda, ubah `UDP_IP` pada `server/udp_sender.py` menjadi alamat IP perangkat yang menjalankan receiver.

## Penjelasan File

### `client/index.html`

File ini adalah halaman antarmuka pengguna. Di dalamnya terdapat dropdown pemilihan kamera, elemen gambar untuk menampilkan frame webcam, dan teks status. Styling dibuat langsung di dalam tag `<style>` sehingga halaman tetap sederhana dan tidak membutuhkan file CSS terpisah.

### `client/app.js`

File ini mengatur interaksi frontend. Ketika dropdown kamera berubah, script mengirim request ke endpoint `/camera`. Script juga menjalankan fungsi `updateFrame()` secara berulang untuk mengambil frame terbaru dari endpoint `/frame` dan menampilkannya ke elemen gambar.

### `client/udp_receiver.py`

File ini bertugas sebagai penerima UDP. Program menerima paket UDP, membaca header, menyimpan chunk berdasarkan `frame_id`, menyusun ulang frame ketika semua chunk sudah diterima, lalu menampilkan hasilnya dengan OpenCV.

### `server/http_server.py`

File ini adalah pusat aplikasi web. Flask digunakan untuk menyediakan halaman web, file JavaScript, endpoint penggantian kamera, dan endpoint pengambilan frame. OpenCV digunakan untuk membaca webcam. Karena kamera dapat diakses oleh beberapa request, program menggunakan `threading.Lock()` untuk menghindari konflik akses.

### `server/udp_sender.py`

File ini bertugas mengambil frame dari HTTP server, memecahnya menjadi beberapa chunk, membuat header untuk setiap chunk, lalu mengirimkannya melalui UDP. Pengiriman dilakukan terus-menerus dengan target 8 FPS.

### `server/utils.py`

File ini berisi dua fungsi utilitas:

1. `compress_frame(frame, quality=50)`
   - Mengubah frame OpenCV menjadi JPEG.
   - Menggunakan parameter kualitas JPEG agar ukuran data lebih kecil.

2. `chunk_data(data, chunk_size=1190)`
   - Memecah data byte menjadi beberapa potongan kecil.
   - Digunakan agar frame JPEG dapat dikirim melalui beberapa paket UDP.

## Analisis Protokol Jaringan

Program ini menggunakan dua mekanisme komunikasi:

### HTTP

HTTP digunakan untuk komunikasi antara browser dan Flask server. Browser mengambil halaman web, file JavaScript, dan frame JPEG melalui endpoint HTTP. Mekanisme ini cocok untuk antarmuka web karena browser dapat langsung menampilkan gambar dari endpoint `/frame`.

### UDP

UDP digunakan untuk simulasi streaming frame. UDP bersifat connectionless dan tidak menjamin paket sampai, tidak menjamin urutan paket, serta tidak menyediakan retransmission otomatis. Karena itu, program menambahkan header sederhana yang berisi `frame_id`, `chunk_id`, dan `total_chunks` agar receiver dapat menyusun ulang frame yang diterima.

Kelebihan UDP pada program ini adalah latensi lebih rendah dan overhead lebih kecil. Kekurangannya adalah frame dapat gagal disusun apabila ada chunk yang hilang.

## Batasan Program

- Program belum memiliki mekanisme deteksi paket hilang.
- Program belum membersihkan `frames_buffer` untuk frame lama yang tidak lengkap.
- UDP sender secara default hanya mengirim ke `127.0.0.1`, sehingga perlu konfigurasi ulang jika digunakan di jaringan berbeda.
- Pilihan kamera pada HTML hanya menyediakan kamera `0` dan `1`.
- Endpoint `/frame` mengambil frame saat request masuk, bukan menggunakan pipeline streaming video penuh seperti MJPEG multipart.
- Status FPS pada halaman HTML masih statis dan belum dihitung secara real-time.


## Screenshot Hasil

G02a

<img width="1900" height="1053" alt="image" src="https://github.com/user-attachments/assets/4eb919af-1d8e-4490-a41b-a996c20e8810" />

<img width="1088" height="570" alt="image" src="https://github.com/user-attachments/assets/126f7ac8-c3ff-4147-a88e-59f489734a23" />

<img width="1038" height="297" alt="image" src="https://github.com/user-attachments/assets/374c4be0-ebb0-4001-af67-adea1cb91d15" />

<img width="991" height="346" alt="image" src="https://github.com/user-attachments/assets/0ce76c4a-9d02-4664-a11b-b4005924287f" />
