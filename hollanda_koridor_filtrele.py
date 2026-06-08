import pandas as pd

# 1. Hollanda ana veri setimizi okuyoruz
dosya_adi = "OCM_Hollanda_Tum_Istasyonlar.csv"
try:
    df = pd.read_csv(dosya_adi)
    print(f"Hollanda ana veri seti yüklendi. Toplam İstasyon: {len(df)}")
except FileNotFoundError:
    print(f"Hata: {dosya_adi} bulunamadı!")
    exit()

# 2. Randstad (Amsterdam - Rotterdam - Lahey - Utrecht) Koridoru için Koordinat Sınırları
# Bu sınırlar Hollanda'nın en yoğun trafik ve şarj ağını içine alan bir kutudur
min_enlem, max_enlem = 51.8, 52.5
min_boylam, max_boylam = 4.1, 5.2

# 3. Sadece bu sınırlar içindeki istasyonları filtreliyoruz
koridor_df = df[
    (df['Enlem'] >= min_enlem) & 
    (df['Enlem'] <= max_enlem) & 
    (df['Boylam'] >= min_boylam) & 
    (df['Boylam'] <= max_boylam)
]

# 4. Gürültülü verileri (her ihtimale karşı) temizliyoruz
koridor_df = koridor_df[~koridor_df['Operator'].isin(['Bilinmiyor', '(Business Owner at Location)'])]

# Indexleri sıfırlayalım
koridor_df = koridor_df.reset_index(drop=True)

# 5. Optimize edilmiş Randstad koridoru veri setini kaydediyoruz
yeni_dosya_adi = "Kritik_Koridor_Hollanda.csv"
koridor_df.to_csv(yeni_dosya_adi, index=False, encoding='utf-8-sig')

print(f"\nFiltreleme Başarılı!")
print(f"Hollanda Randstad megapol koridorunda toplam {len(koridor_df)} adet yüksek kaliteli istasyon tespit edildi.")
print(f"Yeni veri seti '{yeni_dosya_adi}' olarak kaydedildi.")

# Randstad Koridorundaki kurumsal rekabet
print("\n--- RANDSTAD KORİDORUNDAKİ OPERATÖR REKABETİ (İlk 5) ---")
print(koridor_df['Operator'].value_counts().head(5))