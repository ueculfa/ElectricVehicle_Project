import requests
import pandas as pd

OCM_API_KEY = "72b12f88-6c6a-44aa-b717-3e8cf463f224"

url = "https://api.openchargemap.io/v3/poi"

headers = {
    "X-API-Key": OCM_API_KEY,
    "User-Agent": "Culfanet_EV_Thesis_Project" 
}

params = {
    "output": "json",
    "countrycode": "TR",
    "maxresults": 5000
}

print("OpenChargeMap sunucularına güvenli bağlantı kuruluyor...")
print("Tüm Türkiye verisi indiriliyor. Lütfen bekleyin...")

response = requests.get(url, headers=headers, params=params)

if response.status_code == 200:
    data = response.json()
    toplam_istasyon = len(data)
    print(f"\nBaşarılı! Türkiye genelinde toplam {toplam_istasyon} adet şarj istasyonu bulundu.\n")
    
    istasyon_listesi = []
    
    for istasyon in data:
        # GÜNCELLEME: Eğer gelen veri 'None' ise (null girilmişse) boş sözlük '{}' kabul et
        address_info = istasyon.get('AddressInfo') or {}
        operator_info = istasyon.get('OperatorInfo') or {}
        usage_type = istasyon.get('UsageType') or {}
        
        istasyon_datasi = {
            "OCM_ID": istasyon.get('ID'),
            "Istasyon_Adi": address_info.get('Title'),
            "Operator": operator_info.get('Title', 'Bilinmiyor'),
            "Enlem": address_info.get('Latitude'),
            "Boylam": address_info.get('Longitude'),
            "Sehir": address_info.get('Town', 'Bilinmiyor'),
            "Kullanim_Tipi": usage_type.get('Title', 'Bilinmiyor'),
            "Priz_Sayisi": istasyon.get('NumberOfPoints') or 0
        }
        istasyon_listesi.append(istasyon_datasi)
    
    df = pd.DataFrame(istasyon_listesi)
    
    dosya_adi = "OCM_Turkiye_Tum_Istasyonlar.csv"
    df.to_csv(dosya_adi, index=False, encoding='utf-8-sig')
    
    print(f"Veri temizleme tamamlandı. Tüm liste '{dosya_adi}' olarak kaydedildi.")
    print("\n--- TÜRKİYE VERİ ÖZETİ (İlk 5 Operatör) ---")
    print(df['Operator'].value_counts().head(5))
    
else:
    print(f"\nHata! Veri çekilemedi.")
    print(f"Durum Kodu: {response.status_code}")