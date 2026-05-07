import requests
from feedgen.feed import FeedGenerator
from datetime import datetime

# Kita tembak langsung API-nya biar datanya dapet semua (gak kosong)
api_url = "https://haji.go.id/api/berita"
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
}

try:
    response = requests.get(api_url, headers=headers, timeout=20)
    response.raise_for_status()
    data = response.json() # API balikin JSON, lebih enak diolah
    # Tergantung struktur API, biasanya ada di data['data'] atau data['results']
    # Di sini kita asumsikan strukturnya data['data']['data'] atau langsung data['data']
    articles = data.get('data', {}).get('data', []) if 'data' in data else []
except Exception as e:
    print(f"Gagal narik data API: {e}")
    exit()

feed = FeedGenerator()
feed.title("Kemenhaj RI News Feed")
feed.link(href="https://haji.go.id/berita", rel='alternate')
feed.description("Berita terkini dari Kementerian Haji dan Umrah RI")

for item in articles:
    entry = feed.add_entry()
    entry.title(item.get('title', 'No Title'))
    entry.content(item.get('excerpt', ''))
    
    # Bikin link absolut
    slug = item.get('slug', '')
    id_berita = item.get('id', '')
    link = f"https://haji.go.id/berita/{slug}-{id_berita}"
    entry.link(href=link)
    
    # Mapping image
    if item.get('image'):
        img_url = item.get('image')
        if not img_url.startswith('http'):
            img_url = f"https://haji.go.id{img_url}"
        entry.enclosure(url=img_url, length=0, type='image/jpeg')

    # Handle tanggal dari API (biasanya ISO format)
    pub_date = item.get('created_at')
    if pub_date:
        try:
            # Parse format ISO dan masukin ke RSS
            dt = datetime.fromisoformat(pub_date.replace('Z', '+00:00'))
            entry.pubDate(dt)
        except:
            pass

# Simpan ke output.xml
with open('output.xml', 'wb') as f:
    f.write(feed.rss_str(pretty=True))

print(f"Berhasil update {len(articles)} berita!")
