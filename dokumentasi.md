# Integrasi ESP32 dan Backend SilaseZ

Dokumen ini menjelaskan kontrak komunikasi IoT yang benar-benar digunakan oleh backend. Untuk instalasi, endpoint REST, dan operasi aplikasi, lihat [README.md](README.md).

## Arsitektur komunikasi

```text
ESP32 -- MQTT --> Mosquitto -- MQTT --> FastAPI --> PostgreSQL
                                           |
                                           +--> REST API / aplikasi klien
```

Aplikasi klien tidak perlu berkomunikasi langsung dengan ESP32. Backend menerima pesan MQTT, memvalidasi status perangkat, lalu menyimpan data perangkat aktif.

## Koneksi MQTT

Docker Compose membuka dua listener Mosquitto:

| Protokol | Host dari mesin pengembang | Port |
|---|---|---|
| MQTT TCP | `localhost` | `1883` |
| MQTT over WebSocket | `localhost` | `9001` |

ESP32 memakai akun `esp_devices`. Kredensial aktual dikelola melalui `docker/mosquitto/config/passwd`; jangan menyimpan kata sandi firmware di repository publik.

Backend memakai akun `backend_admin`, dengan nilai koneksi yang dibaca dari `.env`.

## Topic

Gunakan `device_id` unik dan stabil untuk setiap ESP32.

| Arah | Topic | Fungsi |
|---|---|---|
| ESP32 → backend | `silasez/device/{device_id}/status` | Status perangkat |
| ESP32 → backend | `silasez/device/{device_id}/sensor` | Pembacaan sensor |
| Backend → ESP32 | `silasez/device/{device_id}/command` | Perintah perangkat (disiapkan oleh ACL, belum dipakai MVP) |

ACL saat ini mengizinkan akun perangkat publish ke topic `status` dan `sensor`, serta subscribe ke topic `command`. Backend mempunyai akses ke seluruh topic di bawah `silasez/#`.

## Payload sensor

Kirim JSON dengan nama field huruf kecil berikut:

```json
{
  "suhu": 29.8,
  "kadar_air": 84.3,
  "ph": 4.2,
  "delta_gas": 370
}
```

| Field | Tipe | Keterangan |
|---|---|---|
| `suhu` | number | Suhu silase dalam °C |
| `kadar_air` | number | Kadar air dalam persen |
| `ph` | number | Nilai pH |
| `delta_gas` | number | Nilai gabungan sensor gas MQ135 |

Jika sebuah field tidak dikirim, implementasi saat ini mengisinya dengan `0`. Firmware sebaiknya tetap selalu mengirim seluruh field agar data tidak ambigu.

`delta_gas` untuk sementara disimpan sebagai nilai methane. Nilai ammonia dan CO2 disimpan sebagai `0` sampai format payload dan sensor gas terpisah tersedia.

Contoh publish untuk pengujian:

```bash
mosquitto_pub \
  -h localhost \
  -p 1883 \
  -u esp_devices \
  -P '<password-device>' \
  -t 'silasez/device/esp32-001/sensor' \
  -m '{"suhu":29.8,"kadar_air":84.3,"ph":4.2,"delta_gas":370}'
```

## Siklus hidup perangkat

1. ESP32 connect ke broker dan publish ke topic status atau sensor.
2. Backend membaca `device_id` dari topic.
3. Jika belum dikenal, backend mendaftarkan perangkat dengan status `pending`.
4. Selama masih `pending`, pesan sensor diabaikan dan belum masuk database.
5. Admin melihat perangkat melalui `GET /admin/devices/pending`.
6. Admin mengaitkan perangkat ke silo melalui `POST /admin/devices/{sensor_id}/approve`.
7. Setelah status `active`, pesan sensor berikutnya disimpan ke database.

## Payload status

Backend menerima JSON apa pun pada topic status dan saat ini hanya mencatatnya ke log aplikasi. Contoh format yang dapat dipakai firmware:

```json
{
  "online": true,
  "firmware_version": "1.0.0"
}
```

Format status belum menjadi kontrak persistence dan dapat dikembangkan kemudian.

## Ketentuan implementasi firmware

- Gunakan JSON valid dan UTF-8.
- Pertahankan `device_id` setelah restart atau flashing ulang.
- Terapkan reconnect dengan backoff saat broker tidak tersedia.
- Jangan publish lebih cepat dari kebutuhan monitoring agar database tidak dipenuhi sampel yang tidak berguna.
- Gunakan timestamp broker/backend sebagai sumber waktu persistence; payload sensor saat ini tidak membaca timestamp dari ESP32.
- Jangan menganggap publish MQTT berhasil hanya karena perangkat tersambung; gunakan QoS yang sesuai dengan kebutuhan firmware.

## Troubleshooting

Jika perangkat tidak muncul pada daftar pending:

- pastikan topic mempunyai tepat empat segmen: `silasez/device/{device_id}/{status|sensor}`;
- periksa username/password MQTT;
- periksa log dengan `docker compose logs -f mosquitto backend`;
- pastikan backend menampilkan `MQTT Connected: 0`.

Jika perangkat muncul tetapi data tidak tersimpan:

- pastikan perangkat sudah di-approve dan berstatus `active`;
- pastikan perangkat sudah dikaitkan ke silo yang benar;
- pastikan key payload menggunakan `suhu`, `kadar_air`, `ph`, dan `delta_gas` (huruf kecil);
- periksa error handler MQTT di log backend.
