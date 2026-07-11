# Panduan Deployment SilaseZ Backend

Panduan ini men-deploy FastAPI, PostgreSQL, dan Mosquitto menggunakan Docker Compose pada VPS Ubuntu. Contoh domain yang digunakan adalah `api.example.com`; ganti dengan domain milik Anda.

## 1. Arsitektur Produksi

```text
Flutter App
    |
 HTTPS / WSS
    |
Nginx (80/443)
    |
FastAPI (127.0.0.1:8002)
    |-- PostgreSQL
    |-- Mosquitto MQTT
    |-- uploads/
```

Port PostgreSQL dan MQTT sebaiknya tidak dibuka ke internet kecuali memang dibutuhkan perangkat dari jaringan luar. Jika MQTT harus publik, gunakan TLS dan firewall.

## 2. Kebutuhan Server

- Ubuntu 22.04 atau 24.04
- Minimal 2 vCPU dan RAM 2 GB
- Docker Engine dan Docker Compose plugin
- Domain yang mengarah ke IP VPS
- Akses SSH dengan user sudo

Instal Docker:

```bash
sudo apt update
sudo apt install -y ca-certificates curl git nginx certbot python3-certbot-nginx
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker "$USER"
newgrp docker
docker --version
docker compose version
```

## 3. Mengambil Source Code

```bash
sudo mkdir -p /opt/silasez
sudo chown "$USER":"$USER" /opt/silasez
git clone https://github.com/yogaananda6677/silasez-backend.git /opt/silasez/backend
cd /opt/silasez/backend
```

Untuk deployment dari branch fitur sebelum merge:

```bash
git fetch origin
git checkout agent/backend-platform-features
```

Untuk produksi normal gunakan branch `main` setelah pull request di-merge.

## 4. Konfigurasi Environment

```bash
cp .env.example .env
chmod 600 .env
nano .env
```

Contoh konfigurasi:

```env
DATABASE_URL=postgresql://silasez:PASSWORD_DB_KUAT@postgres:5432/silasez
SECRET_KEY=GANTI_DENGAN_RANDOM_SECRET
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

MQTT_HOST=mosquitto
MQTT_PORT=1883
MQTT_USERNAME=backend_admin
MQTT_PASSWORD=PASSWORD_MQTT_BACKEND

GEMINI_API_KEY=API_KEY_GOOGLE_AI_STUDIO
GEMINI_MODEL=gemini-2.5-flash
```

Generate secret JWT:

```bash
openssl rand -hex 48
```

Jangan pernah commit `.env`, API key, database dump, atau password broker.

## 5. Menyiapkan Kredensial MQTT

File password Mosquitto tidak disimpan di Git. Buat ulang pada server:

```bash
mkdir -p docker/mosquitto/config docker/mosquitto/data docker/mosquitto/log
docker run --rm -it \
  -v "$PWD/docker/mosquitto/config:/mosquitto/config" \
  eclipse-mosquitto:2 \
  mosquitto_passwd -c /mosquitto/config/passwd backend_admin

docker run --rm -it \
  -v "$PWD/docker/mosquitto/config:/mosquitto/config" \
  eclipse-mosquitto:2 \
  mosquitto_passwd /mosquitto/config/passwd esp_devices

chmod 600 docker/mosquitto/config/passwd
```

Password `backend_admin` harus sama dengan `MQTT_PASSWORD` pada `.env`. Firmware ESP menggunakan akun `esp_devices`.

## 6. Menjalankan Container dan Migration

```bash
docker compose up -d --build
docker compose ps
docker compose exec backend alembic upgrade head
```

Migration wajib dijalankan setiap deployment karena beberapa fitur bergantung pada perubahan schema, termasuk tipe pesan video.

Verifikasi:

```bash
curl http://127.0.0.1:8002/
curl http://127.0.0.1:8002/docs
docker compose logs --tail=100 backend
```

## 7. Membatasi Port dengan Firewall

```bash
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'
sudo ufw enable
sudo ufw status
```

Untuk produksi, hapus mapping publik PostgreSQL dari `docker-compose.yml` atau bind hanya ke localhost:

```yaml
ports:
  - "127.0.0.1:5433:5432"
```

FastAPI juga sebaiknya dibind ke localhost:

```yaml
ports:
  - "127.0.0.1:8002:8000"
```

Jika MQTT dipakai ESP melalui internet, buka hanya port yang dibutuhkan dan sebaiknya konfigurasi listener TLS `8883`.

## 8. Konfigurasi Nginx

Buat file:

```bash
sudo nano /etc/nginx/sites-available/silasez-api
```

Isi:

```nginx
server {
    listen 80;
    server_name api.example.com;

    client_max_body_size 30M;

    location /ws/ {
        proxy_pass http://127.0.0.1:8002;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_read_timeout 3600s;
    }

    location / {
        proxy_pass http://127.0.0.1:8002;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 120s;
    }
}
```

Aktifkan:

```bash
sudo ln -s /etc/nginx/sites-available/silasez-api /etc/nginx/sites-enabled/silasez-api
sudo nginx -t
sudo systemctl reload nginx
```

## 9. HTTPS dan WebSocket Secure

```bash
sudo certbot --nginx -d api.example.com
sudo certbot renew --dry-run
```

Setelah HTTPS aktif:

- REST API: `https://api.example.com`
- WebSocket: `wss://api.example.com/ws/chat/{room_id}`
- Dokumentasi: `https://api.example.com/docs`

Ubah base URL aplikasi mobile agar menunjuk ke domain HTTPS tersebut.

## 10. Deployment Update

Setelah perubahan sudah di-merge ke `main`:

```bash
cd /opt/silasez/backend
git fetch origin
git checkout main
git pull --ff-only origin main
docker compose build backend
docker compose up -d
docker compose exec backend alembic upgrade head
docker compose ps
docker compose logs --tail=100 backend
```

Urutan yang aman adalah build image, jalankan container, lalu migration. Untuk perubahan schema yang tidak backward-compatible, gunakan maintenance window.

## 11. Backup dan Restore PostgreSQL

Backup:

```bash
mkdir -p backups
docker compose exec -T postgres pg_dump -U silasez -d silasez -Fc > "backups/silasez-$(date +%F-%H%M).dump"
```

Restore:

```bash
docker compose exec -T postgres pg_restore \
  -U silasez -d silasez --clean --if-exists < backups/NAMA_FILE.dump
```

Backup juga direktori `uploads/` karena foto profil dan lampiran chat disimpan di sana.

## 12. Rollback

Lihat commit sebelumnya:

```bash
git log --oneline -10
```

Checkout commit stabil tanpa menghapus data:

```bash
git checkout COMMIT_STABIL
docker compose up -d --build
```

Jangan menjalankan `alembic downgrade` tanpa backup dan pemeriksaan migration. Migration enum PostgreSQL tertentu tidak dapat dibalik secara otomatis.

## 13. Pemeriksaan Setelah Deployment

```bash
curl -fsS https://api.example.com/
curl -fsS https://api.example.com/openapi.json > /dev/null
docker compose exec backend alembic current
docker compose ps
docker compose logs --tail=100 backend
```

Uji manual:

1. Login peternak, pakar, dan admin.
2. Kirim pesan teks dan lampiran chat.
3. Pastikan badge unread dan status dibaca berubah.
4. Publish perangkat MQTT baru dan cek notifikasi admin.
5. Approve perangkat ke silo dan cek notifikasi peternak.
6. Kirim pertanyaan dan foto ke AI Assistant.
7. Pastikan upload dapat diakses melalui `/static/chat/...`.

## 14. Troubleshooting

```bash
docker compose logs -f backend
docker compose logs -f postgres
docker compose logs -f mosquitto
docker compose restart backend
```

- `401`: token hilang atau kedaluwarsa.
- `403`: role tidak memiliki akses ke resource.
- `422`: payload atau field multipart tidak sesuai.
- Gemini gagal: periksa `GEMINI_API_KEY`, akses internet container, dan model.
- MQTT gagal: periksa password file, ACL, username, dan topic.
- Upload gagal: periksa ukuran, ekstensi, permission direktori `uploads/`, dan `client_max_body_size` Nginx.
