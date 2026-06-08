import osmnx as ox
import pandas as pd
import matplotlib.pyplot as plt
import networkx as nx
import warnings
warnings.filterwarnings('ignore')

print("🌍 OSMnx Graf Altyapısı Başlatılıyor...")

# 1. Hangi veriyi ve hangi şehri inceleyeceğimizi seçiyoruz
# Elindeki Final_NLP dosyalarından birini seç. Örnek: Belçika (Brüksel) veya Almanya (Münih)
DOSYA_ADI = "Final_NLP_Belcika.csv" 
HEDEF_SEHIR = "Brussels" # Burayı CSV'deki şehirlerden birine göre değiştirebilirsin (Örn: 'Paris', 'Istanbul', 'Munich')

# Veriyi yükle
df = pd.read_csv(DOSYA_ADI)

# Eğer spesifik şehir filtrelemek istersen (Biz şimdilik haritada o şehre yakın koordinatları OSMnx ile çekeceğiz)
# Şehrin koordinatlarına göre yol ağını indir
print(f"-> {HEDEF_SEHIR} için gerçek otoyol (Drive) grafı indiriliyor. Lütfen bekleyin (1-2 dk sürebilir)...")
# 'drive' sadece araç yollarını getirir.
G = ox.graph_from_place(f"{HEDEF_SEHIR}", network_type='drive') 

# 2. Şarj İstasyonlarımızı Bu Gerçek Yollara Oturtma (Node Matching)
# Verimizdeki istasyonlardan Brüksel sınırları içinde olanları bulalım (Yaklaşık koordinat sınırları)
# Basitlik için tüm Belçika verisini G grafına yollayacağız, OSMnx dışarıda kalanları umursamayacak.

istasyon_renkleri = []
istasyon_boyutlari = []
enlemler = []
boylamlar = []

print("-> İstasyonlar gerçek yol düğümlerine (Nodes) eşleştiriliyor...")
for index, row in df.iterrows():
    # Sadece o şehre ait veya merkeze yakın verileri haritaya basalım
    # G.nodes'un sınırları içinde mi diye kontrol etmeye gerek yok, ox nearest node bulur ama uzaksa saçmalar.
    # Bu yüzden sadece tutum skoru olanları toplayıp ekrana basacağız.
    enlemler.append(row['Enlem'])
    boylamlar.append(row['Boylam'])
    
    # NLP Skoruna Göre Renklendirme
    if row['Tutum_Skoru'] > 0:
        istasyon_renkleri.append('green')  # Güvenilir
        istasyon_boyutlari.append(50)
    elif row['Tutum_Skoru'] < 0:
        istasyon_renkleri.append('red')    # Riskli/Şikayetli
        istasyon_boyutlari.append(100)     # Kırmızıları daha büyük göster (Risk vurgusu)
    else:
        istasyon_renkleri.append('orange') # Nötr
        istasyon_boyutlari.append(30)

# İstasyonların graf üzerindeki en yakın düğümlerini bulma (Gerçek yola oturtma)
nearest_nodes = ox.distance.nearest_nodes(G, X=boylamlar, Y=enlemler)

# 3. Grafı Çizdirme (Makale Kalitesinde Görsel)
print("-> Çizim oluşturuluyor...")
fig, ax = ox.plot_graph(G, show=False, close=False, edge_color='#999999', edge_linewidth=0.5, node_size=0, bgcolor='white')

# Orijinal CSV'mizdeki istasyonları grafın üzerine saçılım (scatter) ile ekliyoruz
ax.scatter(boylamlar, enlemler, c=istasyon_renkleri, s=istasyon_boyutlari, alpha=0.7, zorder=5, edgecolors='black')

plt.title(f"OSMnx NLP Ağırlıklı Şarj Grafı - {HEDEF_SEHIR}", fontsize=15, color='black')
plt.tight_layout()

# Görseli yüksek çözünürlüklü makale formatında kaydet
plt.savefig(f"OSMnx_Graf_{HEDEF_SEHIR}.png", dpi=300, bbox_inches='tight')
print(f"🎉 İşlem Tamamlandı! Graf resmi 'OSMnx_Graf_{HEDEF_SEHIR}.png' olarak kaydedildi.")
plt.show()