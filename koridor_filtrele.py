import pandas as pd

# 1. Ana veri setimizi okuyoruz
dosya_adi = "OCM_Turkiye_Tum_Istasyonlar.csv"
try:
    df = pd.read_csv(dosya_adi)
    print(f"Ana veri seti yüklendi. Toplam İstasyon: {len(df)}")
except FileNotFoundError:
    print(f"Hata: {dosya_adi} bulunamadı!")
    exit()

# 2. İstanbul - Bursa - İzmir Koridoru için Koordinat Sınırları (Bounding Box)
# Bu sınırlar otoyol güzergahını ve çevresindeki şehirleri kapsar
min_enlem, max_enlem = 38.0, 41.2
min_boylam, max_boylam = 26.5, 30.0

# 3. Pandas ile sadece bu sınırlar içindeki istasyonları filtreliyoruz
koridor_df = df[
    (df['Enlem'] >= min_enlem) & 
    (df['Enlem'] <= max_enlem) & 
    (df['Boylam'] >= min_boylam) & 
    (df['Boylam'] <= max_boylam)
]

# 4. Unknown (Bilinmeyen) operatörleri veri setimizden çıkararak temizliği artırıyoruz
koridor_df = koridor_df[koridor_df['Operator'] != '(Unknown Operator)']

# Indexleri sıfırlayalım ki temiz dursun
koridor_df = koridor_df.reset_index(drop=True)

# 5. Yeni ve optimize edilmiş veri setini kaydediyoruz
yeni_dosya_adi = "Kritik_Koridor_Istasyonlari.csv"
koridor_df.to_csv(yeni_dosya_adi, index=False, encoding='utf-8-sig')

print(f"\nFiltreleme Başarılı!")
print(f"Stratejik koridorda toplam {len(koridor_df)} adet yüksek kaliteli istasyon tespit edildi.")
print(f"Yeni veri seti '{yeni_dosya_adi}' olarak kaydedildi.")

# Koridordaki operatör rekabetine bakalım
print("\n--- KORİDORDAKİ OPERATÖR REKABETİ (İlk 5) ---")
print(koridor_df['Operator'].value_counts().head(5))