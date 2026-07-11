# SilaseZ Backend

Backend SilaseZ adalah layanan API dan IoT untuk memantau proses fermentasi silase. Aplikasi dibangun dengan FastAPI, PostgreSQL, SQLAlchemy/Alembic, MQTT, dan WebSocket.

## Fitur utama

- Registrasi dan autentikasi JWT untuk peternak, pakar, dan admin.
- Pengelolaan peternakan dan silo.
- Pencatatan siklus fermentasi per silo.
- Penerimaan data sensor ESP32 melalui MQTT.
- Registrasi otomatis perangkat baru dan persetujuan perangkat oleh admin.
- Konsultasi peternak–pakar melalui REST API dan WebSocket.
- Unggah foto profil dan penyajian berkas statis.
- Dokumentasi API interaktif dari FastAPI.

## Arsitektur

```text
ESP32 -- MQTT --> Mosquitto --> FastAPI --> PostgreSQL
                                |   |
                                |   +--> WebSocket chat
                                +------> REST API --> aplikasi klien
```

Kode aplikasi mengikuti pemisahan tanggung jawab berikut:

```text
app/
├── api/           # Route REST dan dependency autentikasi
├── core/          # Konfigurasi, database, keamanan, dan enum
├── crud/          # Operasi persistence/database
├── db/            # Seeder data awal
├── models/        # Model SQLAlchemy
├── mqtt/          # Client, topic, dan handler pesan MQTT
├── schemas/       # Model request/response Pydantic
├── services/      # Aturan bisnis aplikasi
├── websocket/     # Koneksi realtime chat
└── main.py        # Entry point FastAPI
```

## Prasyarat

Cara paling sederhana adalah menggunakan Docker:

- Docker Engine
- Docker Compose

Untuk menjalankan tanpa Docker:

- Python 3.12
- PostgreSQL
- MQTT broker (misalnya Mosquitto)

## Konfigurasi

Salin konfigurasi contoh:

```bash
cp .env.example .env
```

Variabel yang tersedia:

| Variabel | Keterangan | Contoh Docker Compose |
|---|---|---|
| `DATABASE_URL` | URL koneksi PostgreSQL | `postgresql://silasez:silasez123@postgres:5432/silasez` |
| `SECRET_KEY` | Kunci penandatanganan JWT; ganti pada production | string acak yang panjang |
| `ALGORITHM` | Algoritma JWT | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Masa berlaku access token | `60` |
| `MQTT_HOST` | Host MQTT broker | `mosquitto` |
| `MQTT_PORT` | Port MQTT | `1883` |
| `MQTT_USERNAME` | Pengguna MQTT backend | `backend_admin` |
| `MQTT_PASSWORD` | Kata sandi MQTT backend | sesuaikan file password Mosquitto |

Kredensial MQTT pada `.env` harus cocok dengan `docker/mosquitto/config/passwd`.

## Menjalankan dengan Docker

```bash
docker compose up -d --build
docker compose exec backend alembic upgrade head
```

Layanan yang tersedia:

| Layanan | Alamat host |
|---|---|
| REST API | `http://localhost:8002` |
| Swagger UI | `http://localhost:8002/docs` |
| ReDoc | `http://localhost:8002/redoc` |
| PostgreSQL | `localhost:5433` |
| MQTT TCP | `localhost:1883` |
| MQTT WebSocket | `localhost:9001` |

Periksa status dan log aplikasi:

```bash
docker compose ps
docker compose logs -f backend
```

Hentikan layanan dengan `docker compose down`. Tambahkan opsi `-v` hanya jika memang ingin menghapus seluruh data PostgreSQL.

## Menjalankan secara lokal

Buat virtual environment dan pasang dependency:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Untuk proses yang berjalan di host, ubah `DATABASE_URL` dan `MQTT_HOST` di `.env` agar menunjuk ke alamat yang dapat diakses dari host, misalnya PostgreSQL pada `localhost:5433` dan MQTT pada `localhost`.

Jalankan migrasi dan server:

```bash
alembic upgrade head
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Dokumentasi Swagger kemudian tersedia di `http://localhost:8000/docs`.

## Autentikasi

Daftarkan peternak melalui `POST /auth/register`, lalu login melalui `POST /auth/login`. Gunakan nilai `access_token` pada endpoint yang dilindungi:

```http
Authorization: Bearer <access_token>
```

Saat startup, aplikasi membuat admin bawaan jika akun tersebut belum ada:

```text
email: admin@silasez.com
password: Admin123!
```

Kredensial tersebut ditujukan untuk bootstrap/development dan wajib diganti untuk deployment production.

Contoh login:

```bash
curl -X POST http://localhost:8002/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"admin@silasez.com","password":"Admin123!"}'
```

## Ringkasan endpoint

Semua endpoint selain root, register, login, dan WebSocket memerlukan bearer token.

| Metode | Endpoint | Keterangan |
|---|---|---|
| `GET` | `/` | Health check sederhana |
| `POST` | `/auth/register` | Registrasi peternak |
| `POST` | `/auth/login` | Login dan memperoleh JWT |
| `GET/PATCH` | `/users/me` | Lihat/perbarui profil |
| `POST` | `/users/me/change-password` | Ganti kata sandi |
| `POST` | `/users/me/photo` | Unggah foto profil (`multipart/form-data`) |
| `GET` | `/users/pakar` | Daftar pengguna pakar |
| `POST/GET` | `/peternakan` | Buat/daftar peternakan milik pengguna |
| `GET/PATCH/DELETE` | `/peternakan/{peternakan_id}` | Detail/perbarui/hapus peternakan |
| `GET` | `/peternakan/{peternakan_id}/riwayat` | Riwayat milik peternak atau pakar terkait |
| `POST/GET` | `/peternakan/{peternakan_id}/silo` | Buat/daftar silo |
| `GET/PATCH/DELETE` | `/silo/{silo_id}` | Detail/perbarui/hapus silo |
| `GET` | `/silo/{silo_id}/sensor/terbaru` | Pembacaan sensor terbaru pada silo |
| `POST` | `/silo/{silo_id}/fermentasi/mulai` | Mulai siklus fermentasi |
| `GET` | `/silo/{silo_id}/fermentasi/aktif` | Siklus yang sedang berjalan |
| `GET` | `/silo/{silo_id}/fermentasi` | Riwayat fermentasi |
| `POST` | `/fermentasi/{cycle_id}/selesai` | Selesaikan/batalkan fermentasi |
| `GET/POST` | `/chat/rooms` | Daftar/buat ruang konsultasi |
| `GET/POST` | `/chat/{room_id}/messages` | Daftar/kirim pesan |
| `PATCH` | `/chat/{room_id}/close` | Tutup ruang konsultasi |
| `POST` | `/admin/pakar` | Buat akun pakar (admin) |
| `GET` | `/admin/devices/pending` | Daftar perangkat menunggu persetujuan (admin) |
| `POST` | `/admin/devices/{sensor_id}/approve` | Assign perangkat ke silo (admin) |
| `GET` | `/pakar/peternakan` | Daftar peternakan dan ringkasan kondisi (pakar) |
| `GET` | `/pakar/peternakan/{peternakan_id}` | Detail kondisi silo, sensor, dan fermentasi aktif (pakar) |
| `GET` | `/pakar/peternakan/{peternakan_id}/riwayat` | Riwayat sensor dan fermentasi (pakar) |
| WebSocket | `/ws/chat/{room_id}` | Menerima broadcast pesan chat realtime |

Format request, response, validasi, dan status code lengkap dapat dicoba langsung melalui Swagger UI.

## Alur perangkat IoT

Backend subscribe ke topic berikut:

```text
silasez/device/+/status
silasez/device/+/sensor
```

Perangkat menerbitkan data menggunakan `device_id` unik:

```text
silasez/device/{device_id}/sensor
```

Contoh payload sensor:

```json
{
  "suhu": 29.8,
  "kadar_air": 84.3,
  "ph": 4.2,
  "delta_gas": 370
}
```

Perangkat yang pertama kali terlihat dibuat dengan status `pending`. Data sensornya belum disimpan sampai admin melakukan approval dan mengaitkannya ke silo. Setelah status menjadi `active`, payload sensor disimpan sebagai log sensor. Saat ini `delta_gas` disimpan sementara pada kolom methane, sedangkan ammonia dan CO2 diisi `0`.

Detail integrasi firmware dan ACL tersedia di [dokumentasi.md](dokumentasi.md).

## Migrasi database

```bash
# Terapkan semua migrasi
alembic upgrade head

# Lihat revisi aktif
alembic current

# Buat migrasi setelah mengubah model
alembic revision --autogenerate -m "deskripsi perubahan"

# Batalkan satu revisi
alembic downgrade -1
```

## Catatan deployment

- Gunakan `SECRET_KEY` yang kuat dan unik.
- Ganti/nonaktifkan kredensial admin bootstrap sebelum production.
- Jangan commit `.env`, database dump, atau kredensial MQTT.
- Batasi port PostgreSQL dan MQTT dari internet jika tidak diperlukan.
- Jalankan `alembic upgrade head` sebagai bagian dari proses release.
- Simpan direktori `uploads/` pada persistent storage jika foto harus bertahan saat container diganti.

Panduan deployment tambahan yang sudah ada dapat dilihat di [PANDUAN_DEPLOY(1).md](PANDUAN_DEPLOY(1).md).
