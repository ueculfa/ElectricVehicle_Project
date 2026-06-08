import pandas as pd
from transformers import pipeline
import time

print("Yapay Zeka (BERT) Modeli Yükleniyor...")
# Türkçe duygu analizi modelimizi çağırıyoruz
duygu_analiz_modeli = pipeline("sentiment-analysis", model="savasy/bert-base-turkish-sentiment-cased")

# Google'dan çektiğimiz devasa yorum dosyasını okutuyoruz
dosya_adi = "Koridor_Tam_Yorumlar.csv"
try:
    df = pd.read_csv(dosya_adi)
except FileNotFoundError:
    print(f"Hata: '{dosya_adi}' bulunamadı!")
    exit()

# Çok kritik: Aynı Google Place ID'den gelen kopya yorumları temizleyelim
onceki_sayi = len(df)
df = df.drop_duplicates(subset=['Google_Place_ID', 'Yorum_Metni']).reset_index(drop=True)
print(f"Kopya yorumlar temizlendi. Kalan benzersiz yorum sayısı: {len(df)}")

tutum_etiketleri = []
tutum_skorlari = []

print(f"\n{len(df)} adet yorum otonom olarak analiz ediliyor. Bu işlem birkaç dakika sürebilir...")
baslangic_zamani = time.time()

for index, yorum in enumerate(df["Yorum_Metni"]):
    # İlerlemeyi görmek için her 50 yorumda bir bilgi verelim
    if index % 50 == 0 and index > 0:
        print(f"  -> {index} yorum analiz edildi...")
        
    kisa_yorum = str(yorum)[:500] 
    
    try:
        sonuc = duygu_analiz_modeli(kisa_yorum)[0]
        etiket = sonuc['label']
        
        if etiket == 'positive':
            tutum_etiketleri.append("Olumlu")
            tutum_skorlari.append(1)
        elif etiket == 'negative':
            tutum_etiketleri.append("Olumsuz")
            tutum_skorlari.append(-1)
        else:
            tutum_etiketleri.append("Nötr")
            tutum_skorlari.append(0)
    except Exception as e:
        # Beklenmedik bir karakter hatası olursa Nötr atayıp devam etsin
        tutum_etiketleri.append("Nötr")
        tutum_skorlari.append(0)

df["Tutum_Etiketi"] = tutum_etiketleri
df["Tutum_Skoru"] = tutum_skorlari

gecen_sure = round(time.time() - baslangic_zamani, 1)

# NLP Analizli yeni veri setini kaydediyoruz
yeni_dosya_adi = "Koridor_NLP_Analizli.csv"
df.to_csv(yeni_dosya_adi, index=False, encoding='utf-8-sig')

print(f"\nİşlem Tamamlandı! Toplam {gecen_sure} saniye sürdü.")
print(f"Skorlanan veriler '{yeni_dosya_adi}' dosyasına kaydedildi.")

# Sonuçların küçük bir analizini ekrana basalım
print("\n--- OTOYOL KORİDORU DUYGU ANALİZİ ÖZETİ ---")
print(df['Tutum_Etiketi'].value_counts())