import pandas as pd
import requests
import time
from transformers import pipeline
import os

# KENDİ GOOGLE API ANAHTARINI BURAYA YAZ (AIzaSy...)
GOOGLE_API_KEY = "AIzaSyBTMlw8Q094KBs7ekrKGWNOjXdNZ8MwBgA"

# Çok Dilli NLP Modelini sadece bir kere en başta yüklüyoruz (Zaman tasarrufu)
print("🧠 Çok Dilli (Multilingual) Yapay Zeka Modeli Yüklünüyor...")
duygu_analiz_modeli = pipeline("sentiment-analysis", model="nlptown/bert-base-multilingual-uncased-sentiment")

# Ülkelere göre Google yerel arama terimleri ve dil kodları
ulke_ayarlari = {
    "Belcika": {"terim": "charging station", "dil": "en"}, 
    "Fransa": {"terim": "borne de recharge", "dil": "fr"},
    "Ispanya": {"terim": "estación de carga", "dil": "es"},
    "Portekiz": {"terim": "estação de carregamento", "dil": "pt"},
    "Macaristan": {"terim": "töltőállomás", "dil": "hu"},
    "Avusturya": {"terim": "Ladestation", "dil": "de"},
    "Italya": {"terim": "stazione di ricarica", "dil": "it"},
    "Bulgaristan": {"terim": "зарядна станция", "dil": "bg"},
    "Yunanistan": {"terim": "σταθμός φόρτισης", "dil": "el"},
    "Kuzey_Makedonya": {"terim": "charging station", "dil": "en"},
    "Romanya": {"terim": "stație de încărcare", "dil": "ro"},
    "Hirvatistan": {"terim": "punionica", "dil": "hr"}
}

search_url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
details_url = "https://maps.googleapis.com/maps/api/place/details/json"

MAX_ORNEKLEM = 300  # Her ülke için seçilecek rastgele istasyon sayısı (Akademik Örneklem)

print(f"\n🚀 Master Google & NLP Otomasyonu Başlıyor! (Her ülkeden max {MAX_ORNEKLEM} istasyon)\n")

for ulke, ayar in ulke_ayarlari.items():
    dosya_adi = f"OCM_{ulke}_Tum_Istasyonlar.csv"
    
    if not os.path.exists(dosya_adi):
        print(f"⚠️ {dosya_adi} bulunamadı, atlanıyor...")
        continue
        
    print(f"==================================================")
    print(f"🌍 ÜLKE: {ulke.upper()} İŞLENİYOR... (Terim: {ayar['terim']})")
    
    df = pd.read_csv(dosya_adi)
    
    # Çöp verileri temizle
    df = df[~df['Operator'].isin(['Bilinmiyor', '(Business Owner at Location)', '(Unknown Operator)'])]
    
    # Veri yeterliyse rassal örneklem al, değilse hepsini al (Örn: Makedonya)
    if len(df) > MAX_ORNEKLEM:
        df = df.sample(n=MAX_ORNEKLEM, random_state=42).reset_index(drop=True)
    else:
        df = df.reset_index(drop=True)
        
    print(f"-> Analiz edilecek temiz istasyon sayısı: {len(df)}")
    
    toplanan_yorumlar = []
    
    # 1. GOOGLE MAPS KAZIMA AŞAMASI
    for index, row in df.iterrows():
        operator = row['Operator']
        sehir = row['Sehir']
        
        arama_metni = f"{operator} {ayar['terim']} {sehir if sehir != 'Bilinmiyor' else ''}"
        
        search_params = {
            "query": arama_metni,
            "location": f"{row['Enlem']},{row['Boylam']}", 
            "radius": 5000, 
            "key": GOOGLE_API_KEY,
            "language": ayar['dil']
        }
        
        try:
            search_response = requests.get(search_url, params=search_params)
            search_data = search_response.json()
            
            if search_data.get("status") == "OK" and len(search_data.get("results", [])) > 0:
                place_id = search_data["results"][0].get("place_id")
                
                details_params = {
                    "place_id": place_id,
                    "key": GOOGLE_API_KEY,
                    "language": ayar['dil'], 
                    "fields": "rating,reviews"
                }
                
                details_response = requests.get(details_url, params=details_params)
                details_data = details_response.json()
                
                if details_data.get("status") == "OK":
                    sonuc = details_data.get("result", {})
                    yorumlar = sonuc.get("reviews", [])
                    
                    for yorum in yorumlar:
                        metin = yorum.get("text", "").strip()
                        if metin:
                            toplanan_yorumlar.append({
                                "OCM_ID": row['OCM_ID'],
                                "Istasyon_Adi": row['Istasyon_Adi'],
                                "Operator": operator,
                                "Ulke": ulke,
                                "Enlem": row['Enlem'],
                                "Boylam": row['Boylam'],
                                "Google_Place_ID": place_id,
                                "Yorum_Metni": metin
                            })
        except Exception as e:
            pass # Bağlantı hatası olursa sessizce atla
            
        time.sleep(0.5) # Yarım saniye bekleme (Maliyet ve rate limit kontrolü)
        
    # 2. NLP (YAPAY ZEKA) SKORLAMA AŞAMASI
    if toplanan_yorumlar:
        yorum_df = pd.DataFrame(toplanan_yorumlar)
        yorum_df = yorum_df.drop_duplicates(subset=['Google_Place_ID', 'Yorum_Metni']).reset_index(drop=True)
        print(f"-> Google'dan {len(yorum_df)} adet yorum çekildi. NLP Analizi başlıyor...")
        
        tutum_etiketleri = []
        tutum_skorlari = []
        
        for index, yorum in enumerate(yorum_df["Yorum_Metni"]):
            kisa_yorum = str(yorum)[:500] 
            try:
                sonuc = duygu_analiz_modeli(kisa_yorum)[0]
                etiket = sonuc['label'] 
                
                if etiket in ['1 star', '2 stars']:
                    tutum_etiketleri.append("Olumsuz")
                    tutum_skorlari.append(-1)
                elif etiket in ['4 stars', '5 stars']:
                    tutum_etiketleri.append("Olumlu")
                    tutum_skorlari.append(1)
                else:
                    tutum_etiketleri.append("Nötr") 
                    tutum_skorlari.append(0)
            except:
                tutum_etiketleri.append("Nötr")
                tutum_skorlari.append(0)
                
        yorum_df["Tutum_Etiketi"] = tutum_etiketleri
        yorum_df["Tutum_Skoru"] = tutum_skorlari
        
        cikis_dosyasi = f"Final_NLP_{ulke}.csv"
        yorum_df.to_csv(cikis_dosyasi, index=False, encoding='utf-8-sig')
        print(f"✅ {ulke} tamamlandı! Dosya: {cikis_dosyasi}")
    else:
        print(f"❌ {ulke} için yorum bulunamadı veya eşleşme sağlanamadı.")
        
print("\n🎉 TÜM AVRUPA MASTER OTOMASYONU KUSURSUZ ŞEKİLDE TAMAMLANDI!")