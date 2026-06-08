import pandas as pd
from transformers import pipeline
import time

print("Çok Dilli (Multilingual) Yapay Zeka Modeli Yükleniyor...")
duygu_analiz_modeli = pipeline("sentiment-analysis", model="nlptown/bert-base-multilingual-uncased-sentiment")

dosya_adi = "Koridor_Hollanda_Tam_Yorumlar.csv"
try:
    df = pd.read_csv(dosya_adi)
except FileNotFoundError:
    print(f"Hata: '{dosya_adi}' bulunamadı!")
    exit()

# Google'dan gelen kopya yorumları (aynı ID ve aynı metin) temizleyelim
df = df.drop_duplicates(subset=['Google_Place_ID', 'Yorum_Metni']).reset_index(drop=True)
print(f"Kopya yorumlar temizlendi. Kalan benzersiz yorum sayısı: {len(df)}")

tutum_etiketleri = []
tutum_skorlari = []

print(f"\n{len(df)} adet Hollandaca/İngilizce yorum otonom olarak analiz ediliyor. Bu işlem birkaç dakika sürebilir...")
baslangic_zamani = time.time()

for index, yorum in enumerate(df["Yorum_Metni"]):
    if index % 100 == 0 and index > 0:
        print(f"  -> {index} yorum analiz edildi...")
        
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
            
    except Exception as e:
        tutum_etiketleri.append("Nötr")
        tutum_skorlari.append(0)

df["Tutum_Etiketi"] = tutum_etiketleri
df["Tutum_Skoru"] = tutum_skorlari

gecen_sure = round(time.time() - baslangic_zamani, 1)

# NLP Analizli yeni veri setini kaydediyoruz
yeni_dosya_adi = "Koridor_Hollanda_NLP_Analizli.csv"
df.to_csv(yeni_dosya_adi, index=False, encoding='utf-8-sig')

print(f"\nİşlem Tamamlandı! Toplam {gecen_sure} saniye sürdü.")
print(f"Skorlanan veriler '{yeni_dosya_adi}' dosyasına kaydedildi.")

# Sonuçların özetini ekrana basalım
print("\n--- HOLLANDA RANDSTAD KORİDORU DUYGU ANALİZİ ÖZETİ ---")
print(df['Tutum_Etiketi'].value_counts())