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
    
    headers = {
        'User-Agent': 'GidaDedektifi - OgrenciProjesi - Version 1.0'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=20)
        
        if response.status_code != 200:
             return jsonify({"durum": "hata", "mesaj": "Sunucuya bağlanılamadı."})

        data = response.json()
        
        if data.get('status') != 1:
            return jsonify({"durum": "bulunamadi", "mesaj": "Ürün veritabanında yok."})

        urun = data['product']
        urun_adi = urun.get('product_name', 'İsimsiz Ürün')
        
        # İçerik metinlerini al
        text_genel = urun.get('ingredients_text', '')
        text_tr = urun.get('ingredients_text_tr', '')
        text_en = urun.get('ingredients_text_en', '')
        text_de = urun.get('ingredients_text_de', '')
        
        # Hepsini birleştir (Analiz için kullanılan ham metin)
        ham_metin = (text_genel + " " + text_tr + " " + text_en + " " + text_de).lower()
        
        # Görsel veriler
        resim_url = urun.get('image_url', '') 
        nutri_score = urun.get('nutriscore_grade', '').upper()

        # Sözlük taraması
        bulunanlar = []
        for anahtar_kelime, deger in MADDELER_SOZLUGU.items():
            if anahtar_kelime in ham_metin:
                if isinstance(deger, dict):
                    aciklama_metni = deger.get("bilgi", "Bilgi yok")
                    risk_puani = deger.get("risk", 0)
                    kaynak_linki = deger.get("kaynak", "") # <--- YENİ EKLENEN
                else:
                    aciklama_metni = deger
                    risk_puani = 0 
                    kaynak_linki = "" # Eski formatta kaynak yok

                bulunanlar.append({
                    "madde": anahtar_kelime.upper(),
                    "bilgi": aciklama_metni,
                    "risk": risk_puani,
                    "kaynak": kaynak_linki  # <--- Frontend'e gönderiyoruz
                })
        
        return jsonify({
            "durum": "basarili",
            "urun": urun_adi,
            "resim": resim_url,
            "puan": nutri_score,
            "analiz_sonucu": bulunanlar,
            "ham_icerik": ham_metin  # <-- DEĞİŞİKLİK BURADA: Artık kesmiyoruz, hepsini gönderiyoruz.
        })

    except Exception as e:
        return jsonify({"durum": "hata", "mesaj": str(e)})


if __name__ == '__main__':
    app.run(debug=True)
