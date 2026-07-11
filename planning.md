# SilaseZ Backend Development Plan

> Last Update: 04 Juli 2026

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

### Sudah selesai

- [x] Membuat struktur project FastAPI
- [x] Menyiapkan Docker
- [x] Menyiapkan Docker Compose
- [x] Menjalankan PostgreSQL
- [x] Menjalankan Mosquitto MQTT
- [x] Menjalankan FastAPI
- [x] Swagger Documentation
- [x] Environment Configuration (.env)
- [x] Database Connection

Status

```
SELESAI
```

---

## ✅ Tahap 2 — Authentication

### Sudah dikerjakan

- [x] Model User
- [x] Schema Register
- [x] Schema Login
- [x] JWT Configuration
- [x] Password Hash
- [x] Auth Router
- [x] Auth Service
- [x] Register Endpoint
- [x] Login Endpoint

Masih terdapat beberapa bug pada proses hashing password yang sedang diperbaiki.

Status

```
90%
```

---

## ✅ Tahap 3 — Database

Sudah

- [x] SQLAlchemy
- [x] Session
- [x] User Model
- [x] Migration dasar
- [x] Relasi awal

Status

```
80%
```

---

## ✅ Tahap 4 — Docker

Sudah

- [x] Dockerfile
- [x] Docker Compose
- [x] Volume
- [x] PostgreSQL
- [x] Mosquitto
- [x] API

Status

```
95%
```

---

# Bug Yang Sudah Diperbaiki

## Import Error

```
ModuleNotFoundError
```

Status

```
Selesai
```

---

## Session Error

```
AttributeError
Session has no attribute db
```

Status

```
Selesai
```

---

## Router Error

Pemanggilan service salah.

Status

```
Selesai
```

---

## Dependency Injection

Perbaikan penggunaan Depends dan Session.

Status

```
Selesai
```

---

## Authentication Service

Perbaikan static method menjadi object service.

Status

```
Selesai
```

---

## Password Hash

Masih terdapat bug pada bcrypt.

Status

```
Dalam Proses
```

---

# Yang Akan Dikerjakan

## Tahap 5 — Menyelesaikan Authentication

- [ ] Memperbaiki bcrypt
- [ ] Register berhasil
- [ ] Login berhasil
- [ ] Generate JWT
- [ ] Verify JWT
- [ ] Middleware Authentication

Estimasi

```
1 Hari
```

---

## Tahap 6 — User Management

- [ ] Get Profile
- [ ] Update Profile
- [ ] Change Password
- [ ] Upload Foto Profil

Estimasi

```
1 Hari
```

---

## Tahap 7 — Peternakan

- [ ] CRUD Peternakan
- [ ] Relasi User
- [ ] Lokasi Peternakan
- [ ] Reverse Geocoding
- [ ] Simpan Latitude Longitude
- [ ] Simpan Provinsi
- [ ] Simpan Kabupaten
- [ ] Simpan Kecamatan
- [ ] Simpan Desa

Estimasi

```
2 Hari
```

---

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
| Authentication | 90% |
| User | 10% |
| Peternakan | 0% |
| Device | 0% |
| MQTT | 0% |
| Monitoring | 0% |
| Kontrol IoT | 0% |
| Notifikasi | 0% |
| Testing | 0% |
| Deployment | 0% |

---

# Target Selanjutnya

Prioritas pengerjaan berikutnya:

1. Menyelesaikan bug hashing password (bcrypt).
2. Menyelesaikan fitur Register dan Login hingga menghasilkan JWT yang valid.
3. Menambahkan middleware autentikasi untuk endpoint yang memerlukan login.
4. Mengembangkan modul manajemen pengguna (profil dan perubahan password).
5. Memulai pengembangan modul Peternakan beserta integrasi lokasi menggunakan reverse geocoding.
6. Mengintegrasikan komunikasi MQTT dengan perangkat IoT untuk monitoring dan kontrol secara real-time.

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