# SilaseZ Backend Development Plan

> Last Update: 04 Juli 2026 (revisi 2)

---

# Gambaran Sistem (Overview)

SilaseZ merupakan sistem manajemen peternakan berbasis IoT yang terdiri dari beberapa layanan (services) yang saling terhubung. Sistem dibangun menggunakan arsitektur client-server dengan REST API sebagai pusat komunikasi data.

## Arsitektur Sistem

```text
                    Flutter Mobile
                          │
                          │ REST API
                          ▼
                FastAPI Backend (Python)
                          │
     ┌────────────────────┼────────────────────┐
     │                    │                    │
     ▼                    ▼                    ▼
 PostgreSQL          Authentication       Business Logic
 Database              (JWT)               Services
     │
     │
     ▼
MQTT Broker (Mosquitto)
     │
     ▼
ESP32 / Sensor IoT
```

---

## Komponen Sistem

### 1. Mobile Application (Flutter)

Digunakan oleh pengguna untuk:

- Login
- Register
- Melihat data peternakan
- Monitoring sensor
- Mengontrol perangkat
- Mengelola data peternakan

---

### 2. FastAPI Backend

Backend bertugas sebagai pusat logika aplikasi.

Fungsinya:

- Authentication
- Authorization
- CRUD Database
- Validasi Data
- JWT
- API Endpoint
- Komunikasi Database
- Komunikasi MQTT

---

### 3. PostgreSQL

Digunakan sebagai penyimpanan data utama.

Contoh data:

- User
- Peternakan
- Sensor
- Riwayat Monitoring
- Riwayat Kontrol
- Device

---

### 4. MQTT Broker (Mosquitto)

Sebagai media komunikasi real-time antara backend dengan perangkat IoT.

Contoh:

ESP32 publish

```
temperature
humidity
water_level
```

Backend subscribe

```
sensor/data
```

Backend publish

```
relay/on
relay/off
```

ESP32 subscribe

```
device/control
```

---

### 5. ESP32

Perangkat IoT yang bertugas membaca sensor dan menerima perintah dari backend.

---

# Struktur Backend

```text
Flutter
    │
REST API
    │
FastAPI
    │
 ├── API Router
 ├── Service
 ├── CRUD
 ├── Security
 ├── Database
 ├── JWT
 └── MQTT
          │
      PostgreSQL
```

---

# Progress Pengerjaan

## ✅ Tahap 1 — Persiapan Project

Status

```
SELESAI
```

---

## ✅ Tahap 2 — Authentication (dasar)

Status

```
SELESAI
```

---

## ✅ Tahap 3 — Database

Status

```
SELESAI
```

---

## ✅ Tahap 4 — Docker

Status

```
SELESAI
```

---

## ✅ Tahap 5 — Menyelesaikan Authentication

- [x] Memperbaiki bcrypt (sudah benar dari awal via SHA-256 normalize)
- [x] Register berhasil
- [x] Login berhasil
- [x] Generate JWT
- [x] Verify JWT
- [x] Middleware Authentication (`get_current_user` via `HTTPBearer`, di `app/api/deps.py`)

Status

```
SELESAI
```

---

## ✅ Tahap 6 — User Management

- [x] Get Profile — `GET /users/me`
- [x] Update Profile — `PATCH /users/me`
- [x] Change Password — `POST /users/me/change-password`
- [x] Upload Foto Profil — `POST /users/me/photo` (validasi ekstensi, max 2MB, static file serving via `/static`)

Status

```
SELESAI (menunggu migration photo_url dijalankan di server — lihat Catatan Bug)
```

---

## ✅ Tahap 7 — Peternakan

- [x] CRUD Peternakan — `POST/GET/PATCH/DELETE /peternakan`
- [x] Relasi User (ownership check: hanya pemilik atau admin yang bisa akses)
- [x] Lokasi Peternakan (tabel `lokasi`, one-to-one dengan `peternakan`)
- [x] Reverse Geocoding — otomatis via Nominatim (OpenStreetMap), gratis tanpa API key
- [x] Simpan Latitude Longitude
- [x] Simpan Provinsi
- [x] Simpan Kabupaten
- [x] Simpan Kecamatan
- [x] Simpan Desa
- [x] Soft delete peternakan

Status

```
SELESAI (reverse geocoding baru divalidasi pakai mock response — belum dites live call ke Nominatim, perlu verifikasi di server yang internetnya kebuka)
```

---

# Bug Yang Sudah Diperbaiki

## Import Error

Status: Selesai

## Session Error (`AttributeError: Session has no attribute db`)

Status: Selesai

## Router Error (pemanggilan service salah)

Status: Selesai

## Dependency Injection (penggunaan `Depends` dan `Session`)

Status: Selesai

## Authentication Service (static method → object service)

Status: Selesai

## Password Hash (bcrypt)

Status: Selesai (normalize password pakai SHA-256 sebelum bcrypt untuk hindari limit 72 byte)

## Login gagal (500 — `ResponseValidationError: Field required 'user'`)

`response_model=TokenResponse` mewajibkan field `user`, tapi router lama cuma balikin `access_token` + `token_type`.

Status: Selesai — router sekarang langsung return hasil lengkap dari `AuthService.login()`.

## Register bocorin password hash

Endpoint register tidak pakai `response_model`, jadi objek `User` mentah (termasuk kolom `password` ter-hash) ikut ke-return di response JSON.

Status: Selesai — ditambahkan `response_model=UserResponse`.

## File duplikat/dead code di `app/api/`

`app/api/router.py` dan `app/api/init.py` (tanpa underscore) adalah file nyasar/duplikat yang tidak pernah dipakai (`app/api/__init__.py` cuma import dari `auth.py`).

Status: Selesai — kedua file dihapus.

## Relationship dobel di model `Silo` dan `Sensor`

Kedua model punya relationship (`peternakan`/`farm`, `sensors`, `silo`, `logs`) yang didefinisikan dua kali (kemungkinan copy-paste), menyebabkan `SAWarning` soal foreign key overlap tiap kali mapper di-configure.

Status: Selesai — duplikasi dihapus, tersisa satu definisi konsisten per relasi.

## `sub` JWT (string) vs kolom `id` (UUID) di `get_current_user`

Query `User.id == user_id` gagal/salah kalau `user_id` masih berupa string mentah dari payload token.

Status: Selesai — dikonversi pakai `uuid.UUID(payload.get("sub"))` sebelum query.

## ⚠️ `column users.photo_url does not exist` (production, belum selesai)

Model `User` sudah punya kolom `photo_url`, tapi migration `75129ad9365e_add_photo_url_to_users.py` belum dijalankan di database server (`silasez_db`). Error muncul di `/auth/register` dan endpoint apa pun yang query tabel `users`.

Status: **Perlu dijalankan manual** di server:
```bash
docker exec -it silasez_api alembic upgrade head
```
Kalau file migration belum ada di dalam container (image lama), rebuild dulu:
```bash
docker compose build silasez_api
docker compose up -d
docker exec -it silasez_api alembic upgrade head
```

---

# Yang Akan Dikerjakan

## Tahap 8 — Device

- [ ] CRUD Device
- [ ] Registrasi ESP32
- [ ] Aktivasi Device
- [ ] Pairing Device

Estimasi

```
2 Hari
```

---

## Tahap 9 — MQTT

- [ ] MQTT Client
- [ ] Subscribe
- [ ] Publish
- [ ] Receive Sensor
- [ ] Simpan Database

Estimasi

```
2 Hari
```

---

## Tahap 10 — Monitoring

- [ ] Sensor Suhu
- [ ] Sensor Kelembaban
- [ ] Sensor Air
- [ ] Riwayat Sensor
- [ ] Dashboard Monitoring

Estimasi

```
2 Hari
```

---

## Tahap 11 — Kontrol IoT

- [ ] Kontrol Relay
- [ ] Kontrol Pompa
- [ ] Kontrol Kipas
- [ ] Kontrol Otomatis

Estimasi

```
2 Hari
```

---

## Tahap 12 — Notifikasi

- [ ] MQTT Alert
- [ ] Push Notification
- [ ] Kondisi Darurat

Estimasi

```
1 Hari
```

---

## Tahap 13 — Testing

- [ ] Unit Test
- [ ] API Test
- [ ] Integration Test
- [ ] Docker Test

Estimasi

```
2 Hari
```

---

## Tahap 14 — Deployment

- [ ] VPS
- [ ] Nginx
- [ ] HTTPS
- [ ] Domain
- [ ] Docker Production

Estimasi

```
2 Hari
```

---

# Progress Keseluruhan

| Modul | Progress |
|---------|---------:|
| Setup Project | 100% |
| Docker | 95% |
| Database | 80% |
| Authentication | 100% |
| User Management | 100%* |
| Peternakan | 100%** |
| Device | 0% |
| MQTT | 0% |
| Monitoring | 0% |
| Kontrol IoT | 0% |
| Notifikasi | 0% |
| Testing | 0% |
| Deployment | 0% |

`*` menunggu migration `photo_url` dijalankan di server production.
`**` reverse geocoding baru divalidasi via mock, belum live-test ke Nominatim.

---

# Target Selanjutnya

Prioritas pengerjaan berikutnya:

1. **[URGENT]** Jalankan `alembic upgrade head` di server untuk kolom `photo_url` yang belum ke-apply.
2. Verifikasi reverse geocoding Nominatim dengan live call di server (bukan mock).
3. Mulai modul **Device**: CRUD device, registrasi ESP32, aktivasi, dan pairing device ke peternakan/silo.
4. Lanjut ke integrasi **MQTT** untuk komunikasi real-time dengan ESP32 (publish/subscribe sensor & kontrol).
5. Modul **Monitoring** dan **Kontrol IoT** setelah MQTT client siap.

---

# Catatan

Backend menggunakan konsep **Clean Architecture** sederhana dengan pemisahan:

- API (Router)
- Service (Business Logic)
- CRUD (Database Access)
- Models (ORM)
- Schemas (Validation)
- Core (Security, Config, Database)
- MQTT Service
- Dependencies

Arsitektur ini dipilih agar kode lebih mudah dikembangkan, diuji, dan dipelihara seiring bertambahnya fitur pada sistem SilaseZ.

**Prosedur wajib setiap kali ada perubahan model/kolom baru:** selalu generate & jalankan migration (`alembic revision` + `alembic upgrade head`) sebelum deploy ulang container, supaya skema database dan model Python selalu sinkron. Bug `photo_url does not exist` di atas adalah contoh nyata akibat lupa langkah ini.
