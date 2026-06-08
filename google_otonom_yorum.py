import pandas as pd
import requests
import time

# BURAYA GOOGLE PLACES API ANAHTARINI YAPISTIR (AIzaSy ile başlayan)
GOOGLE_API_KEY = "AIzaSyBTMlw8Q094KBs7ekrKGWNOjXdNZ8MwBgA"

# 1. Koridor veri setimizi okuyoruz
dosya_adi = "Kritik_Koridor_Istasyonlari.csv"
try:
    df = pd.read_csv(dosya_adi)
except FileNotFoundError:
    print(f"Hata: {dosya_adi} bulunamadı!")
    exit()

# 2. GÜVENLİK KİLİDİ: Sistemi test etmek için şimdilik sadece İLK 10 İSTASYONU alıyoruz
test_df = df
print(f"Otomasyon başlatılıyor... {len(test_df)} adet istasyon için Google taranacak.\n")

toplanan_yorumlar = []

# Google API Endpoint'leri
search_url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
details_url = "https://maps.googleapis.com/maps/api/place/details/json"

for index, row in test_df.iterrows():
    operator = row['Operator']
    sehir = row['Sehir']
    
    # İstasyonu Google'da bulmak için akıllı bir arama metni oluşturuyoruz
    # OCM'de "Bilinmiyor" yazan şehirleri aramaya katmamak için ufak bir kontrol:
    arama_metni = f"{operator} şarj istasyonu {sehir if sehir != 'Bilinmiyor' else ''}"
    
    print(f"Aranıyor: {arama_metni} (OCM ID: {row['OCM_ID']})")
    
    # ADIM A: İstasyonun Google Place ID'sini bulma
    search_params = {
        "query": arama_metni,
        "location": f"{row['Enlem']},{row['Boylam']}", # OCM'deki koordinatlara yakın yerleri önceliklendir
        "radius": 5000, # 5 km yarıçapında ara
        "key": GOOGLE_API_KEY,
        "language": "tr"
    }
    
    search_response = requests.get(search_url, params=search_params)
    search_data = search_response.json()
    
    if search_data.get("status") == "OK" and len(search_data.get("results", [])) > 0:
        # En mantıklı (ilk) eşleşmeyi alıyoruz
        en_iyi_eslesme = search_data["results"][0]
        place_id = en_iyi_eslesme.get("place_id")
        google_isim = en_iyi_eslesme.get("name")
        
        print(f"  Eşleşme Bulundu -> Google'daki Adı: {google_isim}")
        
        # ADIM B: Bulunan Place ID ile yorumları çekme
        details_params = {
            "place_id": place_id,
            "key": GOOGLE_API_KEY,
            "language": "tr",
            "fields": "rating,reviews"
        }
        
        details_response = requests.get(details_url, params=details_params)
        details_data = details_response.json()
        
        if details_data.get("status") == "OK":
            sonuc = details_data.get("result", {})
            genel_puan = sonuc.get("rating", "Puan Yok")
            yorumlar = sonuc.get("reviews", [])
            
            # NLP modelimize göndermek üzere sadece metin içeren yorumları listeye ekliyoruz
            for yorum in yorumlar:
                metin = yorum.get("text", "").strip()
                if metin:
                    toplanan_yorumlar.append({
                        "OCM_ID": row['OCM_ID'],
                        "Istasyon_Adi": row['Istasyon_Adi'],
                        "Operator": operator,
                        "Sehir": sehir,
                        "Google_Place_ID": place_id,
                        "Genel_Puan": genel_puan,
                        "Verilen_Yildiz": yorum.get("rating"),
                        "Yorum_Metni": metin
                    })
    else:
        print("  Bu istasyon için Google'da eşleşme bulunamadı veya sonuç boş.")
    
    # API sınırlarına takılmamak (Rate Limit) için her istasyondan sonra 1 saniye bekliyoruz
    time.sleep(1)

# 3. Sonuçları yeni bir tabloya kaydetme
if toplanan_yorumlar:
    yorum_df = pd.DataFrame(toplanan_yorumlar)
    cikti_dosyasi = "Koridor_Tam_Yorumlar.csv"
    yorum_df.to_csv(cikti_dosyasi, index=False, encoding='utf-8-sig')
    print(f"\nİşlem Tamam! {len(yorum_df)} adet yorum başarıyla '{cikti_dosyasi}' dosyasına kaydedildi.")
else:
    print("\nEşleşen veya metin içeren yorum bulunamadı.")