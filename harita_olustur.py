import pandas as pd
import folium

print("Veriler birleştiriliyor ve harita oluşturuluyor...")

# 1. İki farklı verisetimizi (Koordinatlar ve NLP Skorları) okuyoruz
try:
    df_nlp = pd.read_csv("Koridor_NLP_Analizli.csv")
    df_koordinat = pd.read_csv("Kritik_Koridor_Istasyonlari.csv")
except FileNotFoundError as e:
    print(f"Hata: {e}")
    exit()

# 2. NLP verilerini istasyon bazında grupluyoruz
istasyon_skorlari = df_nlp.groupby('OCM_ID')['Tutum_Skoru'].mean().reset_index()

# 3. Skorlar ile Koordinatları OCM_ID üzerinden birleştiriyoruz
harita_verisi = pd.merge(df_koordinat, istasyon_skorlari, on='OCM_ID', how='inner')

# 4. Haritayı Oluşturuyoruz
merkez_enlem = harita_verisi['Enlem'].mean()
merkez_boylam = harita_verisi['Boylam'].mean()
m = folium.Map(location=[merkez_enlem, merkez_boylam], zoom_start=8, tiles='CartoDB positron')

# 5. İstasyonları tek tek haritaya işliyoruz
for idx, row in harita_verisi.iterrows():
    skor = row['Tutum_Skoru']
    
    if skor > 0:
        renk = 'green'   
        ikon = 'ok-sign'
    elif skor < 0:
        renk = 'red'     
        ikon = 'remove-sign'
    else:
        renk = 'gray'    
        ikon = 'info-sign'
        
    popup_text = f"""
    <div style='width: 200px'>
        <b>{row['Istasyon_Adi']}</b><br>
        Operatör: {row['Operator']}<br>
        Şehir: {row['Sehir']}<br>
        <b>Yapay Zeka Skoru: {skor:.2f}</b>
    </div>
    """
    
    folium.Marker(
        location=[row['Enlem'], row['Boylam']],
        popup=folium.Popup(popup_text, max_width=300),
        icon=folium.Icon(color=renk, icon=ikon)
    ).add_to(m)

# 6. BİLGİ KUTUSU (LEJANT) EKLENTİSİ
legend_html = '''
     <div style="
     position: fixed; 
     bottom: 50px; right: 50px; width: 200px; height: 160px; 
     border:2px solid grey; z-index:9999; font-size:14px;
     background-color:white; padding: 10px; border-radius: 8px; box-shadow: 2px 2px 5px rgba(0,0,0,0.3);
     ">
     <b>Yapay Zeka Skorları</b><br>
     <i>Duygu Analizi (NLP) Eğilimi</i><br><br>
     <i class="glyphicon glyphicon-ok-sign" style="color:green"></i>&nbsp; Olumlu (Güvenilir)<br>
     <i class="glyphicon glyphicon-info-sign" style="color:gray"></i>&nbsp; Nötr (Veri Yetersiz)<br>
     <i class="glyphicon glyphicon-remove-sign" style="color:red"></i>&nbsp; Olumsuz (Riskli)
      </div>
     '''
m.get_root().html.add_child(folium.Element(legend_html))

# 7. Haritayı HTML dosyası olarak kaydediyoruz
cikis_dosyasi = "Otoyol_Yapay_Zeka_Haritasi.html"
m.save(cikis_dosyasi)

print(f"\nİşlem Tamam! Toplam {len(harita_verisi)} istasyon haritaya işlendi.")
print(f"Lütfen klasöründeki '{cikis_dosyasi}' dosyasına çift tıklayarak tarayıcında aç.")