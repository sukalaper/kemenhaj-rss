import requests
from feedgen.feed import FeedGenerator
from datetime import datetime, timezone, timedelta

# Jangan tembak URL Berita (HTML), tembak API-nya langsung
api_url = "https://haji.go.id/api/v1/news?limit=10&page=1"
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Accept': 'application/json'
}

try:
    response = requests.get(api_url, headers=headers, timeout=20)
    response.raise_for_status()
    # Website ini biasanya balikin JSON
    res_json = response.json()
    
    # Struktur standar API biasanya ada di ['data'] atau ['results']
    # Kita coba ambil list beritanya
    articles = res_json.get('data', [])
    if not isinstance(articles, list):
        articles = res_json.get('data', {}).get('data', [])
        
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
    
    # Excerpt/Deskripsi
    entry.description(item.get('excerpt', ''))
    
    # Link berita (biasanya slug + id)
    slug = item.get('slug', '')
    id_news = item.get('id', '')
    entry.link(href=f"https://haji.go.id/berita/{slug}-{id_news}")
    
    # Gambar
    if item.get('image_url'):
        entry.enclosure(url=item.get('image_url'), length=0, type='image/jpeg')
    
    # Tanggal
    pub_date_str = item.get('created_at')
    if pub_date_str:
        try:
            # Parse ISO format dari API
            dt = datetime.fromisoformat(pub_date_str.replace('Z', '+00:00'))
            entry.pubDate(dt)
        except:
            pass

with open('output.xml', 'wb') as f:
    f.write(feed.rss_str(pretty=True))

print(f"Mantap! Berhasil dapet {len(articles)} berita dari API.")
