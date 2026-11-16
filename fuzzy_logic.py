import numpy as np

def trapmf(x, params):
    """Fungsi keanggotaan Trapesium [a, b, c, d]."""
    a, b, c, d = params
    y = np.zeros_like(x, dtype=float)

    if b > a:
        idx_naik = (x > a) & (x < b)
        y[idx_naik] = (x[idx_naik] - a) / (b - a)

    y[(x >= b) & (x <= c)] = 1.0

    if d > c:
        idx_turun = (x > c) & (x < d)
        y[idx_turun] = (d - x[idx_turun]) / (d - c)
    return y

def trimf(x, params):
    """Fungsi keanggotaan Segitiga [a, b, c]."""
    a, b, c = params
    y = np.zeros_like(x, dtype=float)

    if b > a:
        idx_naik = (x > a) & (x <= b)
        y[idx_naik] = (x[idx_naik] - a) / (b - a)

    if c > b:
        idx_turun = (x > b) & (x < c)
        y[idx_turun] = (c - x[idx_turun]) / (c - b)
    return y

def _eval_trap(val, params):
    return float(trapmf(np.array([val], dtype=float), params)[0])

def _eval_tri(val, params):
    return float(trimf(np.array([val], dtype=float), params)[0])

def _bangun_basis_aturan():
    """Menghasilkan 81 kombinasi aturan IF-THEN (3x3x3x3) budidaya ikan nila."""
    rules = []
    suhu_sets = ['Dingin', 'Normal', 'Panas']
    ph_sets = ['Asam', 'Normal', 'Basa']
    keruh_sets = ['Jernih', 'Sedang', 'Keruh']
    bobot_sets = ['Kecil', 'Sedang', 'Besar']

    nomor = 1
    for s in suhu_sets:
        for p in ph_sets:
            for k in keruh_sets:
                for b in bobot_sets:
                    if s in ('Dingin', 'Panas'):
                        # Suhu ekstrem menurunkan nafsu makan ikan secara drastis
                        if p == 'Normal' and k == 'Jernih' and b == 'Besar':
                            output = 'Sedang'
                        else:
                            output = 'Sedikit'
                    else:  # Suhu Normal
                        if p == 'Normal':
                            if k == 'Jernih':
                                output = 'Sedang' if b == 'Kecil' else 'Banyak'
                            elif k == 'Sedang':
                                if b == 'Besar':
                                    output = 'Banyak'
                                elif b == 'Sedang':
                                    output = 'Sedang'
                                else:
                                    output = 'Sedikit'
                            else:  # Kekeruhan Keruh
                                output = 'Sedang' if b == 'Besar' else 'Sedikit'
                        else:  # pH Asam atau Basa
                            if k == 'Keruh':
                                output = 'Sedikit'
                            elif k == 'Sedang':
                                output = 'Sedang' if b == 'Besar' else 'Sedikit'
                            else:  # Kekeruhan Jernih
                                output = 'Sedang' if b in ('Sedang', 'Besar') else 'Sedikit'

                    rules.append({
                        'no': f"{nomor:02d}",
                        'suhu': s,
                        'ph': p,
                        'kekeruhan': k,
                        'bobot': b,
                        'output': output
                    })
                    nomor += 1
    return rules

BASIS_ATURAN = _bangun_basis_aturan()

def cek_kelayakan_air(suhu, ph, kekeruhan):
    """Mengevaluasi kondisi keselamatan kualitas air sebelum pemberian pakan."""
    alasan = []
    if suhu < 21.0 or suhu > 34.0:
        alasan.append(f"suhu air ekstrem ({suhu}°C)")
    if ph < 5.5 or ph > 9.0:
        alasan.append(f"pH air berbahaya ({ph})")
    if kekeruhan > 85.0:
        alasan.append(f"kekeruhan terlalu tinggi ({kekeruhan} NTU)")
    if alasan:
        return False, f"Pakan ditunda karena {', '.join(alasan)}."
    return True, "Kondisi air mendukung pemberian pakan."

def hitung_dosis_fuzzy(suhu, ph, kekeruhan, bobot):
    """
    Menjalankan proses Fuzzy Mamdani lengkap:
    1. Fuzzifikasi -> 2. Evaluasi 81 Aturan (MIN) -> 3. Agregasi (MAX) -> 4. Defuzzifikasi Centroid.
    """
    #Fuzzifikasi tiap variabel masukan
    mu_suhu = {
        'Dingin': _eval_trap(suhu, [20, 20, 24, 26]),
        'Normal': _eval_tri(suhu, [24, 28, 32]),
        'Panas': _eval_trap(suhu, [30, 32, 35, 35]),
    }
    mu_ph = {
        'Asam': _eval_trap(ph, [4, 4, 6, 6.5]),
        'Normal': _eval_tri(ph, [6, 7.5, 8.5]),
        'Basa': _eval_trap(ph, [8, 9, 10, 10]),
    }
    mu_keruh = {
        'Jernih': _eval_trap(kekeruhan, [0, 0, 15, 30]),
        'Sedang': _eval_tri(kekeruhan, [15, 45, 75]),
        'Keruh': _eval_trap(kekeruhan, [60, 80, 100, 100]),
    }
    mu_bobot = {
        'Kecil': _eval_trap(bobot, [10, 10, 50, 150]),
        'Sedang': _eval_tri(bobot, [50, 200, 350]),
        'Besar': _eval_trap(bobot, [250, 400, 500, 500]),
    }

    # Semesta variabel keluaran: Dosis Pakan (0 - 100%)
    z = np.linspace(0, 100, 1001)
    mf_output = {
        'Sedikit': trapmf(z, [0, 0, 25, 50]),
        'Sedang': trimf(z, [25, 50, 75]),
        'Banyak': trapmf(z, [50, 75, 100, 100]),
    }

    agregasi = np.zeros_like(z)
    aturan_aktif = []

    for rule in BASIS_ATURAN:
        alpha = min(
            mu_suhu[rule['suhu']],
            mu_ph[rule['ph']],
            mu_keruh[rule['kekeruhan']],
            mu_bobot[rule['bobot']]
        )
        if alpha > 0:
            implikasi = np.minimum(alpha, mf_output[rule['output']])
            agregasi = np.maximum(agregasi, implikasi)

            aturan_aktif.append({
                'no': rule['no'],
                'alpha': round(alpha, 2),
                'if_text': (
                    f"IF Suhu {rule['suhu']} AND pH {rule['ph']} "
                    f"AND Kekeruhan {rule['kekeruhan']} AND Bobot {rule['bobot']} (α = {alpha:.2f})"
                ),
                'then_text': f"THEN Dosis {rule['output']}"
            })

    # Urutkan aturan aktif berdasarkan kekuatan terbesar
    aturan_aktif.sort(key=lambda item: item['alpha'], reverse=True)

    # 4. Defuzzifikasi Centroid
    if np.sum(agregasi) == 0:
        dosis_crisp = 50.0
    else:
        dosis_crisp = float(np.sum(z * agregasi) / np.sum(agregasi))

    dosis_final = round(dosis_crisp, 1)
    layak, keterangan_air = cek_kelayakan_air(suhu, ph, kekeruhan)

    if not layak:
        return {
            'dosis': 0.0,
            'kategori': 'Tunda Pakan',
            'status_layak': False,
            'status_teks': 'Status Air: Tidak Layak (Tunda Pakan)',
            'status_ket': keterangan_air,
            'aturan': aturan_aktif
        }

    if dosis_final < 37.5:
        kategori = 'Dosis Sedikit'
    elif dosis_final <= 62.5:
        kategori = 'Dosis Sedang'
    else:
        kategori = 'Dosis Banyak'

    return {
        'dosis': dosis_final,
        'kategori': kategori,
        'status_layak': True,
        'status_teks': 'Status Air: Layak',
        'status_ket': keterangan_air,
        'aturan': aturan_aktif
    }