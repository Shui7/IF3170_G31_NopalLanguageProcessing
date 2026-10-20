# IF3170_G31_NopalLanguageProcessing

Tugas Besar 1 IF3170 Inteligensi Artifisial 2026/2027.

## Pembagian Tugas

| NIM | Nama | Tugas |
|---|---|---|
| 13524003 | Faiq Azzam Nafidz | Objective function utama (score()), Genetic Algorithm, GUI, visualisasi state, plotting, dan laporan. |
| 13524013 | Anindya Naufal Pinasthika | State & Objective function, pembangkitan neighbor,  simulated annealing, bonus alternatif objective function, dan laporan |
| 13524139 | Azri Arzaq Pohan | State, hill climbing (Steepest Ascent), bonus implementasi seluruh algoritma hill-climbing (Sideways Move, Random-Restart, Stochastic), dan laporan |

Tugas besar ini dibuat untuk melakukan searching konfigurasi pengisian paket ke dalam peti kemas truk yang **memaksimalkan nilai (*value*)** paket yang diangkut dengan menggunakan algoritma *local search*. 
Setiap paket dapat berada di dalam ataupun di luar truk, dengan *constraint* yang telah ditetapkan sebagai berikut:
- Paket tidak boleh melayang, saling tumpang tindih, atau menembus dinding peti kemas,
- Barang terpecah-belah (*fragile*) tidak boleh menjadi penopang paket lain,
- Total berat tidak boleh melebihi kapasitas maksimum truk.

Algoritma yang diimplementasikan:

| Algoritma | Varian |
|---|---|
| Hill Climbing | Steepest Ascent, Sideways Move (*maximum sideways move*), Random Restart (*maximum restart*), Stochastic |
| Simulated Annealing | Suhu awal, *cooling rate*, maksimum iterasi |
| Genetic Algorithm | Jumlah populasi, banyak iterasi |

Fungsi objektif:
- **Maximize score**: total *value* paket di dalam truk dikurangi penalti pelanggaran *constraint*.
- **Maximize packet count**: jumlah paket di dalam truk (bonus: fungsi objektif alternatif).

Program menampilkan visualisasi 3D *initial state* dan *final state*, juga plot nilai fungsi objektif terhadap iterasi (serta plot e^(ΔE/T) untuk Simulated Annealing dan plot nilai maksimum & rata-rata populasi untuk Genetic Algorithm), dan statistik hasil pencarian.

## Setup

Requirements: **Python 3.12 or newer**.

```bash
python3 -m venv venv
source venv/bin/activate
python -m pip install -r requirements.txt
```

## Cara Menjalankan
Jalankan dari *root* repository:

```bash
python -m src.main
```

1. Klik **Select file** untuk memilih file input `.json`, atau isi data truk dan paket secara manual dengan **Add package**.
2. Pilih fungsi objektif dan algoritma, lalu atur parameternya.
3. **Run** untuk menjalankan pencarian.
4. **Save Result** untuk menyimpan hasil ke file `.txt`, misalnya ke folder `output/`.

### Linux/WSL yang menggunakan Python Conda

Kalau muncul pesan seperti ini saat menjalankan programnya di WSL `QOpenGLWidget: Failed to create context`, jalankan program dengan command berikut:

```bash
LD_PRELOAD=/usr/lib/x86_64-linux-gnu/libstdc++.so.6 \
QT_QPA_PLATFORM=xcb \
./venv/bin/python -m src.main
```

### Format File Input

```json
{
  "truck": { "length": 100, "width": 60, "height": 60, "max_capacity": 400 },
  "packages": [
    { "id": "P1", "length": 40, "width": 30, "height": 20, "weight": 25, "value": 120, "fragile": false }
  ]
}
```
