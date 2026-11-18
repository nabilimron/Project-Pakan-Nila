from flask import Flask, render_template, request
from fuzzy_logic import hitung_dosis_fuzzy

app = Flask(__name__)


def validasi_dan_parsing(form):
    """Memvalidasi masukan agar berupa angka dan berada dalam semesta pembicaraan."""
    batas = {
        'suhu': ('Suhu Air', 20.0, 35.0, '°C'),
        'ph': ('pH Air', 4.0, 10.0, ''),
        'kekeruhan': ('Kekeruhan', 0.0, 100.0, 'NTU'),
        'bobot': ('Bobot Ikan', 10.0, 500.0, 'gram'),
    }

    data = {}
    errors = []

    for key, (label, min_val, max_val, satuan) in batas.items():
        raw = form.get(key, '').strip()
        if raw == '':
            errors.append(f"{label} tidak boleh kosong.")
            continue
        try:
            nilai = float(raw)
        except ValueError:
            errors.append(f"{label} harus berupa angka yang valid.")
            continue

        if nilai < min_val or nilai > max_val:
            errors.append(
                f"{label} harus berada di antara {min_val} dan {max_val} {satuan}.".strip()
            )
        else:
            data[key] = nilai

    return data, errors


@app.route('/')
def beranda():
    return render_template('beranda.html', active_page='beranda')


@app.route('/sistem', methods=['GET', 'POST'])
def sistem():
    input_data = {
        'suhu': 28.0,
        'ph': 7.5,
        'kekeruhan': 15.0,
        'bobot': 200.0
    }
    errors = []

    if request.method == 'POST':
        parsed_data, errors = validasi_dan_parsing(request.form)
        input_data.update(parsed_data)

    hasil = hitung_dosis_fuzzy(
        input_data['suhu'],
        input_data['ph'],
        input_data['kekeruhan'],
        input_data['bobot']
    )

    return render_template(
        'sistem.html',
        active_page='sistem',
        input_data=input_data,
        hasil=hasil,
        errors=errors
    )


@app.route('/tentang')
def tentang():
    return render_template('tentang.html', active_page='tentang')


if __name__ == '__main__':
    app.run(debug=True, port=5001)