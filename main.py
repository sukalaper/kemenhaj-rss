from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
import requests
from datetime import datetime, timezone, timedelta
import re

# URL Target Kemenhaj
url = "https://haji.go.id/berita"
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
}

try:
    # Narik data asli dari web
    response = requests.get(url, headers=headers, timeout=20)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'html.parser')
except Exception as e:
    print(f"Gagal narik data: {e}")
    exit()

# Cari semua container berita
news_cards = soup.find_all('div', class_='news-card')
articles = []

month_map = {
    'januari': 'January', 'februari': 'February', 'maret': 'March',
    'april': 'April', 'mei': 'May', 'juni': 'June',
    'juli': 'July', 'agustus': 'August', 'september': 'September',
    'oktober': 'October', 'november': 'November', 'desember': 'December'
}

for card in news_cards:
    # 1. Judul & Link
    title_elem = card.find('h3', class_='news-card-title')
    title = title_elem.text.strip() if title_elem else "No Title"
    
    link_elem = card.find('a', class_='news-card-title-link')
    link = link_elem.get('href', '')
    if link.startswith('/'):
        link = 'https://haji.go.id' + link

    # 2. Konten/Excerpt
    excerpt_elem = card.find('p', class_='news-card-excerpt')
    content = excerpt_elem.text.strip() if excerpt_elem else ""

    # 3. Gambar
    img_elem = card.find('img')
    image_url = img_elem.get('src') if img_elem else None

    # 4. Tanggal (Format: 7 Mei 2026)
    date_elem = card.find('span', class_='news-card-date')
    published_date = None
    if date_elem:
        date_text = date_elem.text.strip().lower()
        match = re.search(r'(\d{1,2})\s+(\w+)\s+(\d{4})', date_text)
        if match:
            day, month_id, year = match.groups()
            month_en = month_map.get(month_id, month_id)
            try:
                date_str = f"{day} {month_en} {year}"
                published_date = datetime.strptime(date_str, "%d %B %Y")
                jakarta_tz = timezone(timedelta(hours=7))
                published_date = published_date.replace(tzinfo=jakarta_tz)
            except ValueError:
                published_date = None

    articles.append({
        'title': title,
        'link': link,
        'content': content,
        'image': image_url,
        'published_date': published_date
    })

# Sort & Filter top 4
articles.sort(key=lambda x: x['published_date'] if x['published_date'] else datetime.min, reverse=True)
articles = articles[:4]

# Create RSS
feed = FeedGenerator()
feed.title("Kemenhaj RI News Feed")
feed.link(href=url, rel='alternate')
feed.description("Berita terkini dari Kementerian Haji dan Umrah RI")

for article in articles:
    entry = feed.add_entry()
    entry.title(article['title'])
    entry.content(article['content'])
    entry.link(href=article['link'])
    if article['published_date']:
        entry.pubDate(article['published_date'])
    if article['image']:
        entry.enclosure(url=article['image'], length=0, type='image/jpeg')

# SIMPAN KE output.xml (Biar sesuai sama struktur folder lo)
with open('output.xml', 'wb') as f:
    f.write(feed.rss_str(pretty=True))

print("RSS Berhasil diperbarui ke output.xml!")
