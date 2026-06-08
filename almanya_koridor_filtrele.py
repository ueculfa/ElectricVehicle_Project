import pandas as pd

# 1. Almanya ana veri setimizi okuyoruz
dosya_adi = "OCM_Almanya_Tum_Istasyonlar.csv"
try:
    df = pd.read_csv(dosya_adi)
    print(f"Almanya ana veri seti yüklendi. Toplam İstasyon: {len(df)}")
except FileNotFoundError:
    print(f"Hata: {dosya_adi} bulunamadı!")
    exit()

# 2. A9 Otoyolu (Münih - Berlin) Koridoru için Koordinat Sınırları (Bounding Box)
# Güneyde Münih (48.0), Kuzeyde Berlin (52.6)
# Doğrusal hattı kapsayacak şekilde dar bir boylam aralığı (11.0 - 13.6)
min_enlem, max_enlem = 48.0, 52.6
min_boylam, max_boylam = 11.0, 13.6

# 3. Sadece bu sınırlar içindeki istasyonları filtreliyoruz
koridor_df = df[
    (df['Enlem'] >= min_enlem) & 
    (df['Enlem'] <= max_enlem) & 
    (df['Boylam'] >= min_boylam) & 
    (df['Boylam'] <= max_boylam)
]

# 4. Gürültülü verileri (Bilinmeyen ve Bireysel İşletmeler) graf modelimizden çıkarıyoruz
koridor_df = koridor_df[~koridor_df['Operator'].isin(['Bilinmiyor', '(Business Owner at Location)'])]

# Indexleri sıfırlayalım
koridor_df = koridor_df.reset_index(drop=True)

# 5. Optimize edilmiş A9 koridoru veri setini kaydediyoruz
yeni_dosya_adi = "Kritik_Koridor_Almanya.csv"
koridor_df.to_csv(yeni_dosya_adi, index=False, encoding='utf-8-sig')

print(f"\nFiltreleme Başarılı!")
print(f"Almanya A9 (Münih-Berlin) koridorunda toplam {len(koridor_df)} adet yüksek kaliteli istasyon tespit edildi.")
print(f"Yeni veri seti '{yeni_dosya_adi}' olarak kaydedildi.")

# A9 Koridorundaki kurumsal rekabet
print("\n--- A9 KORİDORUNDAKİ OPERATÖR REKABETİ (İlk 5) ---")
print(koridor_df['Operator'].value_counts().head(5))