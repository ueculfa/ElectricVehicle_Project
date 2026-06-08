import pandas as pd
from transformers import pipeline

# 1. Hugging Face'ten Türkçe Duygu Analizi modelini yüklüyoruz
# NOT: Kodu ilk çalıştırdığında modeli (yaklaşık 400MB) indireceği için biraz bekletebilir.
print("Yapay Zeka (BERT) modeli yükleniyor... (İlk sefere mahsus 1-2 dakika sürebilir)")
duygu_analiz_modeli = pipeline("sentiment-analysis", model="savasy/bert-base-turkish-sentiment-cased")

# 2. Önceki adımda oluşturduğumuz CSV dosyasını okutuyoruz
dosya_adi = "sarj_istasyonlari_yorumlar.csv"
try:
    df = pd.read_csv(dosya_adi)
    print(f"\nDosya okundu. Toplam {len(df)} adet yorum analiz ediliyor...")
except FileNotFoundError:
    print(f"Hata: '{dosya_adi}' bulunamadı. Önce veri toplama kodunu çalıştırdığına emin ol.")
    exit()

# 3. Sonuçları tutacağımız listeler
tutum_etiketleri = []
tutum_skorlari = []

# 4. Her bir yorumu modele okutup skorluyoruz
for yorum in df["Yorum_Metni"]:
    # Modellerin kelime sınırı vardır, metni stringe çevirip güvenli uzunlukta tutuyoruz
    kisa_yorum = str(yorum)[:500] 
    
    # NLP Modeline tahmini yaptırıyoruz
    sonuc = duygu_analiz_modeli(kisa_yorum)[0]
    etiket = sonuc['label']
    
    # Modeli matematiksel bir 'Tutum Skoruna' çeviriyoruz (Senin asıl kullanacağın veri bu)
    if etiket == 'positive':
        tutum_etiketleri.append("Olumlu")
        tutum_skorlari.append(1)   # STGCN Graf Modeli için +1 Ağırlık
    elif etiket == 'negative':
        tutum_etiketleri.append("Olumsuz")
        tutum_skorlari.append(-1)  # STGCN Graf Modeli için -1 Ağırlık
    else:
        tutum_etiketleri.append("Nötr")
        tutum_skorlari.append(0)

# 5. Yeni skorlarımızı ana tablomuza sütun olarak ekliyoruz
df["Tutum_Etiketi"] = tutum_etiketleri
df["Tutum_Skoru"] = tutum_skorlari

# 6. Yapay zeka ile zenginleştirilmiş yeni veri setini kaydediyoruz
yeni_dosya_adi = "istasyonlar_NLP_analizli.csv"
df.to_csv(yeni_dosya_adi, index=False, encoding='utf-8-sig')

print(f"\nAnaliz Tamamlandı! Zekaya kavuşan veriler '{yeni_dosya_adi}' dosyasına kaydedildi.")
print("\n--- İLK 5 YORUMUN MODEL TARAFINDAN PUANLANMASI ---")
# Ekranda kolay okumak için sadece gerekli sütunları yazdırıyoruz
print(df[["Kullanici_Puani", "Yorum_Metni", "Tutum_Etiketi", "Tutum_Skoru"]].head())