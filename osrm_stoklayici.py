import pandas as pd
import numpy as np
from scipy.spatial import cKDTree
import requests
import time
import glob
import os

print("🛰️ OSRM Gerçek Otoyol İndirme Botu Başladı (Genişletilmiş Menzil ve Tam Veri Seti)...")

# 1. Dashboard ile BİREBİR AYNI verileri yükleme mantığı
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
tree = cKDTree(coords)

# k değerini 3'ten 4'e çıkardık (Daha fazla alternatif komşu bulsun)
distances, indices = tree.query(coords, k=4)

e_lats, e_lons = [], []
toplam_istek = len(coords)

print(f"📌 Toplam {toplam_istek} istasyon için rota hesaplanacak. Bu işlem ağın seyrekliğine göre biraz vakit alabilir...")

for i in range(len(coords)):
    if i % 100 == 0 and i > 0:
        print(f"   -> {i} / {toplam_istek} istasyon işlendi...")
        
    for j in range(1, 4):
        # Eşiği 1.5 dereceden (~150km), 5.0 dereceye (~500km) çıkardık!
        # Artık Türkiye ve Doğu Avrupa'daki uzak istasyonlar da birbirini bulup bağlanacak.
        if distances[i][j] < 5.0: 
            lon1, lat1 = coords[i][1], coords[i][0]
            lon2, lat2 = coords[indices[i][j]][1], coords[indices[i][j]][0]
            
            try:
                url = f"http://router.project-osrm.org/route/v1/driving/{lon1},{lat1};{lon2},{lat2}?overview=simplified&geometries=geojson"
                r = requests.get(url, timeout=5)
                data = r.json()
                
                if data.get("code") == "Ok":
                    route_coords = data["routes"][0]["geometry"]["coordinates"]
                    for pt in route_coords:
                        e_lons.append(pt[0])
                        e_lats.append(pt[1])
                    e_lons.append(None)
                    e_lats.append(None)
                else:
                    e_lats.extend([lat1, lat2, None])
                    e_lons.extend([lon1, lon2, None])
            except:
                e_lats.extend([lat1, lat2, None])
                e_lons.extend([lon1, lon2, None])
            
            time.sleep(0.05) 

rota_df = pd.DataFrame({'Enlem': e_lats, 'Boylam': e_lons})
rota_df.to_csv("Gercek_Otoyol_Rotalari.csv", index=False)
print("🎉 İŞLEM TAMAM! Tüm ülkeleri kapsayan yeni yollar başarıyla stoklandı.")