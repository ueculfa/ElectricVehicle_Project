import pandas as pd
import requests
import time

# BURAYA KENDİ GOOGLE PLACES API ANAHTARINI YAPISTIR (AIzaSy ile başlayan)
GOOGLE_API_KEY = "AIzaSyBTMlw8Q094KBs7ekrKGWNOjXdNZ8MwBgA"

dosya_adi = "Kritik_Koridor_Hollanda.csv"
try:
    df = pd.read_csv(dosya_adi)
except FileNotFoundError:
    print(f"Hata: {dosya_adi} bulunamadı!")
    exit()

print(f"Randstad Megapolü Otomasyonu başlatılıyor... Toplam {len(df)} adet istasyon taranacak.\n")

toplanan_yorumlar = []

search_url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
details_url = "https://maps.googleapis.com/maps/api/place/details/json"

# Hollanda için 3553 istasyonun tamamını (test_df yapmadan) tarıyoruz
for index, row in df.iterrows():
    operator = row['Operator']
    sehir = row['Sehir']
    
    # Hollandaca (Felemenkçe) "Laadpaal" kelimesini kullanıyoruz
    arama_metni = f"{operator} Laadpaal {sehir if sehir != 'Bilinmiyor' else ''}"
    
    # Ekrana çok fazla yazı basıp terminali şişirmemek için her 50 istasyonda bir bilgi verelim
    if index % 50 == 0:
        print(f"[{index}/{len(df)}] Taranıyor... (Son aranan: {arama_metni})")
    
    search_params = {
        "query": arama_metni,
        "location": f"{row['Enlem']},{row['Boylam']}", 
        "radius": 5000, 
        "key": GOOGLE_API_KEY,
        "language": "nl" # Dil: Nederlands (Felemenkçe)
    }
    
    try:
        search_response = requests.get(search_url, params=search_params)
        search_data = search_response.json()
        
        if search_data.get("status") == "OK" and len(search_data.get("results", [])) > 0:
            en_iyi_eslesme = search_data["results"][0]
            place_id = en_iyi_eslesme.get("place_id")
            
            details_params = {
                "place_id": place_id,
                "key": GOOGLE_API_KEY,
                "language": "nl", 
                "fields": "rating,reviews"
            }
            
            details_response = requests.get(details_url, params=details_params)
            details_data = details_response.json()
            
            if details_data.get("status") == "OK":
                sonuc = details_data.get("result", {})
                genel_puan = sonuc.get("rating", "Puan Yok")
                yorumlar = sonuc.get("reviews", [])
                
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
    except Exception as e:
        print(f"Ağ hatası: {e}")
        
    time.sleep(1) # API Rate Limit koruması

if toplanan_yorumlar:
    yorum_df = pd.DataFrame(toplanan_yorumlar)
    cikti_dosyasi = "Koridor_Hollanda_Tam_Yorumlar.csv"
    yorum_df.to_csv(cikti_dosyasi, index=False, encoding='utf-8-sig')
    print(f"\nİşlem Tamam! Toplam {len(yorum_df)} adet yorum başarıyla '{cikti_dosyasi}' dosyasına kaydedildi.")
else:
    print("\nEşleşen veya metin içeren yorum bulunamadı.")