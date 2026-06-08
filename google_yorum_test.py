import requests

# Kendi Google API anahtarın
GOOGLE_API_KEY = "AIzaSyBTMlw8Q094KBs7ekrKGWNOjXdNZ8MwBgA" 

# Bir önceki adımdan aldığımız Trugo Şarj İstasyonu'nun Place ID'si
PLACE_ID = "ChIJDZ32l0IRyhQR7kelbcQRwhE"

# Google Places Details Endpoint'i (Yorumları almak için)
url = "https://maps.googleapis.com/maps/api/place/details/json"

# Sadece isim, genel puan ve yorumları isteyerek veriyi optimize ediyoruz
params = {
    "place_id": PLACE_ID,
    "key": GOOGLE_API_KEY,
    "language": "tr",
    "fields": "name,rating,reviews" 
}

print("Kullanıcı yorumları ve tutum verileri çekiliyor...")
response = requests.get(url, params=params)
data = response.json()

if data.get("status") == "OK":
    sonuc = data.get("result", {})
    print(f"\nİstasyon: {sonuc.get('name')}")
    print(f"Genel Puan: {sonuc.get('rating')}/5.0\n")
    
    yorumlar = sonuc.get("reviews", [])
    if yorumlar:
        print("--- SON KULLANICI YORUMLARI ---")
        for i, yorum in enumerate(yorumlar, 1):
            print(f"Verilen Puan: {yorum.get('rating')}/5")
            print(f"Kullanıcı Yorumu: {yorum.get('text')}")
            print("-" * 40)
    else:
        print("Bu istasyon için metin tabanlı bir yorum bulunamadı.")
else:
    print("Bir hata oluştu!")
    print(f"Durum: {data.get('status')}")