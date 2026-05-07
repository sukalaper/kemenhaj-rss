import requests
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
from datetime import datetime
import re

# URL Target Kemenhaj Berita
url = "https://haji.go.id/berita"
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
}

try:
    response = requests.get(url, headers=headers, timeout=20)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'html.parser')
except Exception as e:
    print(f"Gagal akses website: {e}")
    exit()

# Cari semua card berita sesuai inspect lo
news_cards = soup.find_all('div', class_='news-card')
articles = []

# Mapping bulan buat convert ke format yang dipahami Python
month_map = {
    'januari': 'January', 'februari': 'February', 'maret': 'March',
    'april': 'April', 'mei': 'May', 'juni': 'June',
    'juli': 'July', 'agustus': 'August', 'september': 'September',
    'oktober': 'October', 'november': 'November', 'desember': 'December'
}

for card in news_cards:
    # 1. Judul & Link
    title_elem = card.find('h3', class_='news-card-title')
    title = title_elem.get_text(strip=True) if title_elem else "No Title"
    
    link_elem = card.find('a', class_='news-card-title-link')
    link = link_elem.get('href', '') if link_elem else ""
    if link.startswith('/'):
        link = 'https://haji.go.id' + link

    # 2. Deskripsi/Excerpt
    excerpt_elem = card.find('p', class_='news-card-excerpt')
    content = excerpt_elem.get_text(strip=True) if excerpt_elem else ""

    # 3. Gambar
    img_elem = card.find('img')
    image_url = img_elem.get('src') if img_elem else None

    # 4. Tanggal (Format di HTML: "7 Mei 2026")
    date_elem = card.find('span', class_='news-card-date')
    published_date = None
    if date_elem:
        date_text = date_elem.get_text(strip=True).lower()
        match = re.search(r'(\d{1,2})\s+(\w+)\s+(\d{4})', date_text)
        if match:
            day, month_id, year = match.groups()
            month_en = month_map.get(month_id, month_id)
            try:
                date_str = f"{day} {month_en} {year}"
                published_date = datetime.strptime(date_str, "%d %B %Y")
            except:
                pass

    articles.append({
        'title': title,
        'link': link,
        'content': content,
        'image': image_url,
        'pubDate': published_date
    })

# Bikin RSS
feed = FeedGenerator()
feed.title("Kemenhaj RI News Feed")
feed.link(href=url, rel='alternate')
feed.description("Berita terkini dari Kementerian Haji dan Umrah RI")

for art in articles:
    entry = feed.add_entry()
    entry.title(art['title'])
    entry.link(href=art['link'])
    entry.description(art['content'])
    if art['pubDate']:
        entry.pubDate(art['pubDate'].replace(tzinfo=datetime.now().astimezone().tzinfo))
    if art['image']:
        entry.enclosure(url=art['image'], length=0, type='image/jpeg')

# Simpan ke output.xml
with open('output.xml', 'wb') as f:
    f.write(feed.rss_str(pretty=True))

print(f"Selesai! Berhasil narik {len(articles)} berita.")
