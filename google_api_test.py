import requests

# Buraya kendi Google API anahtarını yapıştır
GOOGLE_API_KEY = "AIzaSyBTMlw8Q094KBs7ekrKGWNOjXdNZ8MwBgA" 

# Google Places Text Search Endpoint'i
url = "https://maps.googleapis.com/maps/api/place/textsearch/json"

# Bursa'daki şarj istasyonlarını aratıyoruz
params = {
    "query": "Elektrikli araç şarj istasyonu Bursa",
    "key": GOOGLE_API_KEY,
    "language": "tr"
}

print("Google Places API'den veriler çekiliyor...")
response = requests.get(url, params=params)
data = response.json()

if data.get("status") == "OK":
    print("Harika! Google Places API başarıyla çalışıyor.\n")
    
    # Bulunan ilk 3 istasyonu yazdıralım
    for i, sonuc in enumerate(data.get("results", [])[:3], 1):
        print(f"{i}. İstasyon: {sonuc.get('name')}")
        print(f"Adres: {sonuc.get('formatted_address')}")
        # Bu 'place_id' ileride yorumları (reviews) çekmek için kilit rol oynayacak
        print(f"Place ID: {sonuc.get('place_id')}") 
        print("-" * 30)
else:
    print("Bir hata oluştu veya anahtar henüz aktif değil.")
    print(f"Durum: {data.get('status')}")
    print(f"Hata Mesajı: {data.get('error_message', 'Bilinmeyen hata')}")