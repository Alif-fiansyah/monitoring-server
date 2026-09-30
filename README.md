# Uptime Monitoring & Telemetry Platform

Uptime Monitoring adalah platform pemantauan server dan *endpoint* modern berbasis web. Dibangun dengan Streamlit dan SQLite, aplikasi ini menyediakan dasboard operator yang interaktif, halaman status publik (*public status page*), inspeksi HTTP header, metrik latensi, pelacakan SSL, serta integrasi webhook Discord untuk notifikasi *outage/incident* secara *real-time*.

---

## 🚀 Fitur Utama

* **Dual View Mode:**
  * **Operator Dashboard (`?view=dashboard`):** Panel manajemen untuk memantau endpoint, menambah target baru, mengatur webhook Discord, dan melihat catatan insiden.
  * **Public Status Page (`?view=status`):** Halaman publik real-time untuk memamerkan status operasional layanan (*system uptime*), lengkap dengan auto-refresh berkala.
* **Telemetri & Inspector Mendalam (`@st.dialog`):** Modal inspeksi interaktif yang menampilkan grafik riwayat latensi, ukuran respons, tipe konten, header web server, dan masa berlaku SSL.
* **Otomasi Pemeriksaan (`worker.py` & GitHub Actions):** Pemeriksaan kesehatan server berjalan otomatis setiap 15 menit menggunakan GitHub Actions (`.github/workflows/ping.yml`).
* **Notifikasi Discord:** Mengirimkan laporan instan secara otomatis ketika layanan mengalami gangguan (*outage*) atau pulih kembali.

---

## 🛠️ Tech Stack

* **Frontend & UI:** Python, Streamlit, Plotly, `streamlit-autorefresh`
* **Backend & Database:** Python, SQLite (`db.py`), Engine & Worker (`engine.py`, `worker.py`)
* **Otomasi & CI/CD:** GitHub Actions (`ping.yml`)
* **Styling & Komponen:** Modular HTML templates (`templates/`) & CSS kustom (`assets/`)

---

## 📂 Struktur Direktori Proyek

```text
├── .github/workflows/   # Otomasi GitHub Actions (ping.yml)
├── assets/              # Aset global termasuk style.css
├── data/                # Data preset konfigurasi (presets.json)
├── templates/           # Komponen UI modular (endpoint_card, kpi_card, status_banner, dll)
├── app.py               # File utama antarmuka Streamlit (Operator & Status Page)
├── db.py                # Skrip manajemen database SQLite
├── engine.py            # Logika inti health check, ping, dan integrasi Discord webhook
├── worker.py            # Skrip background worker yang dijalankan oleh GitHub Actions
├── ui_helpers.py        # Helper untuk memuat template UI dan CSS
└── requirements.txt     # Daftar dependensi Python
```
## Installation & Setup

### 1. Clone the Repository
```bash
git clone [https://github.com/Alif-fiansyah/monitoring-server.git](https://github.com/Alif-fiansyah/monitoring-server.git)
cd monitoring-server
```
### 2. Instal dependensi Python
```bash
pip install -r requirements.txt
```
### 3. Jalankan aplikasi Streamlit
```bash
streamlit run app.py
```

