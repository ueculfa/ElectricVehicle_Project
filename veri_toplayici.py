import requests
import pandas as pd # Eğer yüklü değilse terminalden: pip install pandas

GOOGLE_API_KEY = "AIzaSyBTMlw8Q094KBs7ekrKGWNOjXdNZ8MwBgA"

# Bir önceki adımdan aldığımız 3 istasyonun Place ID'leri
istasyonlar = [
    {"isim": "Zes Şarj İstasyonu (İzmir Yolu)", "place_id": "ChIJK1xc71ARyhQRR-fektkkWaA"},
    {"isim": "Zes Şarj İstasyonu (Korupark)", "place_id": "ChIJnS9pNwAVyhQRSC8_1v4JpXc"},
    {"isim": "Trugo Şarj İstasyonu (Ertuğrul)", "place_id": "ChIJDZ32l0IRyhQR7kelbcQRwhE"}
]

url = "https://maps.googleapis.com/maps/api/place/details/json"
toplanan_veriler = []

print("Google'dan yorumlar çekiliyor ve temizleniyor...")

for istasyon in istasyonlar:
    params = {
        "place_id": istasyon["place_id"],
        "key": GOOGLE_API_KEY,
        "language": "tr",
        "fields": "name,rating,reviews"
    }
    
    response = requests.get(url, params=params)
    data = response.json()
    
    if data.get("status") == "OK":
        sonuc = data.get("result", {})
        yorumlar = sonuc.get("reviews", [])
        
        for yorum in yorumlar:
            # Boşlukları temizle
            metin = yorum.get("text", "").strip() 
            
            # NLP için SADECE metni olan (boş olmayan) yorumları listeye ekle
            if metin: 
                toplanan_veriler.append({
                    "Istasyon_Adi": istasyon["isim"],
                    "Place_ID": istasyon["place_id"],
                    "Kullanici_Puani": yorum.get("rating"),
                    "Yorum_Metni": metin
                })

# Sözlük listesini Pandas DataFrame tablosuna dönüştür
df = pd.DataFrame(toplanan_veriler)

# Türkçe karakter sorunu yaşamamak için utf-8-sig ile CSV olarak kaydet
dosya_adi = "sarj_istasyonlari_yorumlar.csv"
df.to_csv(dosya_adi, index=False, encoding='utf-8-sig')

print(f"\nİşlem Tamamlandı! Toplam {len(df)} adet anlamlı yorum '{dosya_adi}' dosyasına kaydedildi.")
print("\nOluşturulan Verisetinin İlk 3 Satırı:")
print(df.head(3))