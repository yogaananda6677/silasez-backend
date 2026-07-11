# Panduan Setelah Update: MQTT Auth + Auto-Register Device

## Ringkasan perubahan

**Backend:**
- `app/core/config.py` — tambah field `MQTT_USERNAME` & `MQTT_PASSWORD` (sebelumnya dipakai tapi tidak didefinisikan → crash saat start)
- `app/core/enums.py` — tambah status `PENDING` ke `SensorStatus`
- `app/models/sensor.py` — `silo_id` sekarang nullable (device bisa ada dulu sebelum diassign ke silo)
- `app/crud/sensor.py`, `app/crud/sensor_log.py` — baru dibuat
- `app/mqtt/handlers.py` — sudah diisi logic (sebelumnya cuma `print()` + TODO): auto-daftarkan device baru sebagai PENDING, simpan data sensor ke `sensor_logs` hanya kalau status sudah ACTIVE
- `app/schemas/sensor.py` — baru dibuat
- `app/services/admin_service.py` + `app/api/admin.py` — endpoint baru:
  - `GET /admin/devices/pending` → list device yang nunggu approval
  - `POST /admin/devices/{sensor_id}/approve` → body `{silo_id, nama, tipe}`, ubah status jadi ACTIVE
- `alembic/versions/a1b2c3d4e5f6_...py` — migration baru (enum `pending` + `silo_id` nullable)
- `docker/mosquitto/config/mosquitto.conf` — auth diaktifkan (`allow_anonymous false`)
- `docker/mosquitto/config/acl.conf` — baru dibuat, batasi akun `esp_devices` cuma bisa akses topic `silasez/device/...`
- `.env` — tambah `MQTT_USERNAME`/`MQTT_PASSWORD` untuk akun backend (placeholder, **wajib diganti**)

**ESP32 (`terbaru.ino`):**
- `mqtt_server` → ganti dari `broker.hivemq.com` (publik) jadi placeholder IP VPS kamu
- `device_id` sekarang **auto-generate** dari chip ID ESP32 (`ESP.getEfuseMac()`), tidak perlu diketik manual
- Topic ikut pola backend: `silasez/device/{device_id}/sensor`, `/status`, `/command`
- Connect pakai kredensial shared `esp_devices` (bukan per-device)
- Subscribe ke topic `command` supaya bisa terima perintah dari backend nantinya
- Publish status `online` saat pertama connect

## Langkah yang WAJIB kamu lakukan sebelum jalan

### 1. Generate password file mosquitto
Jalankan di VPS (folder project, tempat `docker-compose.yml` berada):
```bash
docker run --rm -v $(pwd)/docker/mosquitto/config:/mosquitto/config eclipse-mosquitto:2 \
  mosquitto_passwd -b /mosquitto/config/passwd backend_admin PASSWORD_BACKEND_KAMU

docker run --rm -v $(pwd)/docker/mosquitto/config:/mosquitto/config eclipse-mosquitto:2 \
  mosquitto_passwd -b /mosquitto/config/passwd esp_devices PASSWORD_ESP_KAMU
```
(command kedua otomatis nambah user ke file yang sama, bukan overwrite)

### 2. Isi kredensial di 3 tempat, harus SAMA persis:
- `.env` → `MQTT_PASSWORD=PASSWORD_BACKEND_KAMU`
- `terbaru.ino` baris `mqtt_password` → `PASSWORD_ESP_KAMU`
- (username sudah fix: `backend_admin` untuk backend, `esp_devices` untuk semua ESP)

### 3. Isi IP/domain VPS di `terbaru.ino`
```cpp
const char* mqtt_server = "IP_ATAU_DOMAIN_VPS_KAMU";
```
ganti dengan IP publik VPS kamu, lalu buka/forward port `1883` di firewall VPS.

### 4. Jalankan migration database
```bash
docker compose exec backend alembic upgrade head
```

### 5. Restart semua service
```bash
docker compose down && docker compose up -d --build
```

## Alur kerja setelah ini jalan
1. ESP32 nyala → connect WiFi → connect MQTT pakai akun `esp_devices` → publish data ke `silasez/device/<chip_id>/sensor`
2. Backend terima data, `device_id` belum ada di DB → otomatis dibuat sebagai sensor **PENDING** (belum tersimpan ke `sensor_logs`, cuma dicatat perangkatnya)
3. Admin panggil `GET /admin/devices/pending` di aplikasi → lihat device baru
4. Admin panggil `POST /admin/devices/{id}/approve` dengan `silo_id` tujuan + nama sensor → status jadi **ACTIVE**
5. Setelah ACTIVE, data sensor selanjutnya baru mulai tersimpan ke `sensor_logs`

## Catatan / belum sempurna, perlu diperhatikan
- **Gas sensor (MQ135)**: firmware ESP cuma kirim 1 nilai gabungan (`delta_gas`), sedangkan tabel `sensor_logs` punya 3 kolom terpisah (`methane`, `ammonia`, `co2`). Untuk sementara nilainya disimpan semua ke kolom `methane`, dan `ammonia`/`co2` diisi `0` — ini sekadar workaround, bukan solusi ideal. Kalau butuh data gas yang akurat per jenis, perlu sensor gas terpisah atau kalibrasi tambahan.
- **Reconnect MQTT**: kalau koneksi MQTT putus di tengah jalan (bukan saat boot), firmware saat ini belum ada logic auto-reconnect otomatis di `loop()` — masih perlu restart manual (ketik `RESET` di Serial). Bisa ditambahkan kalau perlu.
- **Broadcast websocket**: baris `manager.broadcast(...)` di `handlers.py` masih di-comment (TODO) — kalau mau data sensor realtime muncul di frontend tanpa refresh, ini perlu diaktifkan & disesuaikan dengan `websocket/manager.py`.
