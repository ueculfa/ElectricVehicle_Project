import pandas as pd
import numpy as np
from scipy.spatial import Delaunay
import requests
import time
import glob
import os

print("🛰️ Delaunay Triangulation (Deniz Geçişleri İptal Edilmiş) Otoyol İndirme Botu Başladı...")

# 1. Verileri yükleme mantığı
df_list = []

eski_dosyalar = [
    ("Koridor_NLP_Analizli.csv", "Kritik_Koridor_Istasyonlari.csv"),
    ("Koridor_Almanya_NLP_Analizli.csv", "Kritik_Koridor_Almanya.csv"),
    ("Koridor_Hollanda_NLP_Analizli.csv", "Kritik_Koridor_Hollanda.csv")
]

for nlp_file, koor_file in eski_dosyalar:
    if os.path.exists(nlp_file) and os.path.exists(koor_file):
        df_nlp = pd.read_csv(nlp_file)
        df_koor = pd.read_csv(koor_file)
        istasyon_skor = df_nlp.groupby('OCM_ID')['Tutum_Skoru'].mean().reset_index()
        df_merged = pd.merge(istasyon_skor, df_koor[['OCM_ID', 'Enlem', 'Boylam']], on='OCM_ID', how='inner')
        df_list.append(df_merged)

yeni_dosyalar = glob.glob("Final_NLP_*.csv")
for f in yeni_dosyalar:
    df_list.append(pd.read_csv(f))

if not df_list:
    print("❌ Hata: Veri dosyaları bulunamadı!")
    exit()

df_harita = pd.concat(df_list, ignore_index=True)
df_harita = df_harita.drop_duplicates(subset=['Enlem', 'Boylam']).reset_index(drop=True)

coords = np.column_stack((df_harita['Enlem'], df_harita['Boylam']))

print("🕸️ Ağlar matematiksel olarak (Delaunay) örülüyor...")
tri = Delaunay(coords)
edges = set()

for simplex in tri.simplices:
    edges.add(tuple(sorted([simplex[0], simplex[1]])))
    edges.add(tuple(sorted([simplex[1], simplex[2]])))
    edges.add(tuple(sorted([simplex[2], simplex[0]])))

e_lats, e_lons = [], []
gecerli_kenarlar = []

for i, j in edges:
    lat1, lon1 = coords[i][0], coords[i][1]
    lat2, lon2 = coords[j][0], coords[j][1]
    
    dist = np.sqrt((lat1 - lat2)**2 + (lon1 - lon2)**2)
    if dist < 5.0: 
        gecerli_kenarlar.append((lat1, lon1, lat2, lon2))

toplam_istek = len(gecerli_kenarlar)
print(f"📌 Toplam {toplam_istek} adet potansiyel bağlantı OSRM ile doğrulanacak (Sadece gerçek yollar çizilecek)...")

for idx, (lat1, lon1, lat2, lon2) in enumerate(gecerli_kenarlar):
    if idx % 100 == 0 and idx > 0:
        print(f"   -> {idx} / {toplam_istek} yol kontrol edildi...")
        
    try:
        url = f"http://router.project-osrm.org/route/v1/driving/{lon1},{lat1};{lon2},{lat2}?overview=simplified&geometries=geojson"
        r = requests.get(url, timeout=5)
        data = r.json()
        
        # GERÇEKÇİLİK FİLTRESİ: Sadece araba yolu (Ok) dönerse çiz!
        if data.get("code") == "Ok":
            route_coords = data["routes"][0]["geometry"]["coordinates"]
            for pt in route_coords:
                e_lons.append(pt[0])
                e_lats.append(pt[1])
            e_lons.append(None)
            e_lats.append(None)
        else:
            # Deniz varsa veya yol yoksa HİÇBİR ŞEY YAPMA (Geç)
            pass
            
    except:
        # Sunucu zaman aşımına uğrarsa dümdüz çizgi çekme, bağlantıyı yoksay.
        pass
    
    time.sleep(0.05) 

rota_df = pd.DataFrame({'Enlem': e_lats, 'Boylam': e_lons})
rota_df.to_csv("Gercek_Otoyol_Rotalari.csv", index=False)
print("🎉 İŞLEM TAMAM! Deniz aşırı sahte geçişler iptal edildi, sadece asfalt yollar stoklandı.")