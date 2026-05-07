import requests
import json
import re
from feedgen.feed import FeedGenerator
from datetime import datetime

url = "https://haji.go.id/berita"
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
}

try:
    response = requests.get(url, headers=headers, timeout=20)
    response.raise_for_status()
    html = response.text

    # Cari data di dalam tag <script id="__NEXT_DATA__">...</script>
    # Ini adalah "bekal" data JSON yang bakal di-render sama React
    match = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', html)
    
    articles = []
    if match:
        json_data = json.loads(match.group(1))
        # Path data di Next.js biasanya: props -> pageProps -> initialData -> data
        # Gue bikin safe navigation biar gak gampang error
        try:
            # Kita coba cari list berita di dalam JSON state-nya
            # Sesuaikan dengan struktur actual (biasanya ada di pageProps)
            raw_items = json_data.get('props', {}).get('pageProps', {}).get('initialData', {}).get('data', [])
            if not raw_items:
                # Fallback path kalau strukturnya beda
                raw_items = json_data.get('props', {}).get('pageProps', {}).get('data', [])
            
            for item in raw_items[:10]:
                articles.append({
                    'title': item.get('title'),
                    'excerpt': item.get('excerpt', ''),
                    'slug': item.get('slug'),
                    'image': item.get('image'),
                    'date': item.get('created_at')
                })
        except Exception as e:
            print(f"Gagal parsing JSON state: {e}")

    # Kalau JSON state gagal, kita gak punya pilihan selain pasrah atau pake Selenium.
    # Tapi biasanya cara __NEXT_DATA__ ini 99% ampuh buat Next.js.

    feed = FeedGenerator()
    feed.title("Kemenhaj RI News Feed")
    feed.link(href=url, rel='alternate')
    feed.description("Berita terkini dari Kementerian Haji dan Umrah RI")

    for art in articles:
        entry = feed.add_entry()
        entry.title(art['title'] or "No Title")
        entry.description(art['excerpt'] or "")
        entry.link(href=f"https://haji.go.id/berita/{art['slug']}")
        
        if art['image']:
            img_url = art['image'] if art['image'].startswith('http') else f"https://haji.go.id{art['image']}"
            entry.enclosure(url=img_url, length=0, type='image/jpeg')
            
        if art['date']:
            try:
                dt = datetime.fromisoformat(art['date'].replace('Z', '+00:00'))
                entry.pubDate(dt)
            except:
                pass

    with open('output.xml', 'wb') as f:
        f.write(feed.rss_str(pretty=True))

    print(f"Selesai! Dapet {len(articles)} berita.")

except Exception as e:
    print(f"Error fatal: {e}")
