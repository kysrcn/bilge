from flask import Flask, render_template, jsonify
import requests
import json  # <--- YENİ EKLENEN: Json kütüphanesi
import os

app = Flask(__name__)

# Dosyadan veriyi okuyan fonksiyon
def sozluk_yukle():
    try:
        print("--- JSON DOSYASI OKUNUYOR... ---")
        with open('maddeler.json', 'r', encoding='utf-8') as f:
            veri = json.load(f)
            print(f"✅ BAŞARILI: Toplam {len(veri)} adet madde hafızaya alındı.")
            print(f"🔍 Yüklenen ilk 3 madde: {list(veri.keys())[:3]}")
            # Anahtarları küçük harfe çevirerek geri döndür (Garanti olsun)
            return {k.lower(): v for k, v in veri.items()}
            
    except FileNotFoundError:
        print("❌ HATA: maddeler.json dosyası klasörde yok!")
        return {}
    except json.JSONDecodeError as e:
        print(f"❌ HATA: JSON dosyasında yazım hatası var! (Virgül veya parantez hatası)")
        print(f"Hata Detayı: {e}")
        return {}
    except Exception as e:
        print(f"❌ BEKLENMEDİK HATA: {e}")
        return {}

# Program başlarken sözlüğü yükle
MADDELER_SOZLUGU = sozluk_yukle()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analiz/<barkod>')
def analiz(barkod):
    url = f"https://world.openfoodfacts.org/api/v0/product/{barkod}.json"
    
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        
        if data.get('status') != 1:
            return jsonify({"durum": "bulunamadi", "mesaj": "Ürün veritabanında yok."})

        urun = data['product']
        urun_adi = urun.get('product_name', 'İsimsiz Ürün')
        
        # Tüm dillerdeki içerikleri birleştirip küçük harfe çevir
        text_genel = urun.get('ingredients_text', '')
        text_tr = urun.get('ingredients_text_tr', '')
        text_en = urun.get('ingredients_text_en', '')
        text_de = urun.get('ingredients_text_de', '')
        icerik_metni = (text_genel + " " + text_tr + " " + text_en + " " + text_de).lower()

        # Sözlükteki maddeleri içerik metninde ara
        bulunanlar = []
        for anahtar_kelime, aciklama in MADDELER_SOZLUGU.items():
            if anahtar_kelime in icerik_metni:
                # Aynı maddeyi (örn: e300 ve ascorbic acid) iki kere eklememek için basit bir kontrol yapılabilir
                # Şimdilik hepsini ekliyoruz.
                bulunanlar.append({
                    "madde": anahtar_kelime.upper(), # E300 gibi görünsün
                    "bilgi": aciklama
                })
        
        return jsonify({
            "durum": "basarili",
            "urun": urun_adi,
            "analiz_sonucu": bulunanlar,
            "ham_icerik": icerik_metni[:150] + "..." # Kullanıcıya içeriğin başını da gösterelim
        })

    except Exception as e:
        return jsonify({"durum": "hata", "mesaj": str(e)})

if __name__ == '__main__':
    app.run(debug=True)
