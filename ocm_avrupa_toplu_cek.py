import requests
import pandas as pd
import time

# KENDİ OCM API ANAHTARINI BURAYA YAZ
OCM_API_KEY = "72b12f88-6c6a-44aa-b717-3e8cf463f224"

url = "https://api.openchargemap.io/v3/poi"
headers = {
    "X-API-Key": OCM_API_KEY,
    "User-Agent": "Culfanet_EV_Thesis_Project" 
}

# Çekeceğimiz 12 Ülkenin Kodları ve İsimleri (Balkanlar eklendi!)
avrupa_ulkeleri = {
    "BE": "Belcika",
    "FR": "Fransa",
    "ES": "Ispanya",
    "PT": "Portekiz",
    "HU": "Macaristan",
    "AT": "Avusturya",
    "IT": "Italya",
    "BG": "Bulgaristan",
    "GR": "Yunanistan",
    "MK": "Kuzey_Makedonya",
    "RO": "Romanya",
    "HR": "Hirvatistan"
}

print("🌍 Genişletilmiş Avrupa Toplu Veri Çekim Otomasyonu Başlatılıyor...\n")

for ulke_kodu, ulke_adi in avrupa_ulkeleri.items():
    print(f"-> {ulke_adi} ({ulke_kodu}) şarj ağı indiriliyor...")
    
    params = {
        "output": "json",
        "countrycode": ulke_kodu,
        "maxresults": 10000  # Her ülke için maksimumu zorluyoruz
    }
    
    try:
        response = requests.get(url, headers=headers, params=params)
        
        if response.status_code == 200:
            data = response.json()
            print(f"   [BAŞARILI] {ulke_adi} genelinde {len(data)} istasyon bulundu.")
            
            istasyon_listesi = []
            for istasyon in data:
                address_info = istasyon.get('AddressInfo') or {}
                operator_info = istasyon.get('OperatorInfo') or {}
                usage_type = istasyon.get('UsageType') or {}
                
                istasyon_listesi.append({
                    "OCM_ID": istasyon.get('ID'),
                    "Istasyon_Adi": address_info.get('Title'),
                    "Operator": operator_info.get('Title', 'Bilinmiyor'),
                    "Enlem": address_info.get('Latitude'),
                    "Boylam": address_info.get('Longitude'),
                    "Sehir": address_info.get('Town', 'Bilinmiyor'),
                    "Kullanim_Tipi": usage_type.get('Title', 'Bilinmiyor'),
                    "Priz_Sayisi": istasyon.get('NumberOfPoints') or 0
                })
            
            df = pd.DataFrame(istasyon_listesi)
            dosya_adi = f"OCM_{ulke_adi}_Tum_Istasyonlar.csv"
            df.to_csv(dosya_adi, index=False, encoding='utf-8-sig')
            print(f"   [KAYDEDİLDİ] Dosya: {dosya_adi}\n")
            
        else:
            print(f"   [HATA] {ulke_adi} çekilemedi. Durum Kodu: {response.status_code}\n")
            
    except Exception as e:
        print(f"   [SİSTEM HATASI] {ulke_adi} için işlem başarısız: {e}\n")
    
    time.sleep(3)

print("🎯 Tüm ülkelerin baz verileri başarıyla çekildi!")