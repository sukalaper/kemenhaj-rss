import requests
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
from datetime import datetime
import re

url = "https://haji.go.id/berita"
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
}

try:
    response = requests.get(url, headers=headers, timeout=20)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'html.parser')
except Exception as e:
    print(f"Error access: {e}")
    exit()

# Cari semua div yang punya class 'news-card'
news_cards = soup.find_all('div', class_='news-card')
articles = []

# Map bulan Indonesia
month_map = {
    'januari': 'January', 'februari': 'February', 'maret': 'March',
    'april': 'April', 'mei': 'May', 'juni': 'June',
    'juli': 'July', 'agustus': 'August', 'september': 'September',
    'oktober': 'October', 'november': 'November', 'desember': 'December'
}

for card in news_cards:
    try:
        # Cari Judul (selector lebih fleksibel)
        title_tag = card.find(['h3', 'div'], class_='news-card-title')
        title = title_tag.get_text(strip=True) if title_tag else "No Title"

        # Cari Link
        link_tag = card.find('a', href=True)
        link = link_tag['href'] if link_tag else ""
        if link.startswith('/'):
            link = 'https://haji.go.id' + link

        # Cari Excerpt
        desc_tag = card.find('p', class_='news-card-excerpt')
        desc = desc_tag.get_text(strip=True) if desc_tag else ""

        # Cari Gambar
        img_tag = card.find('img')
        img_url = img_tag.get('src') if img_tag else None

        # Cari Tanggal
        date_tag = card.find('span', class_='news-card-date')
        pub_date = None
        if date_tag:
            d_text = date_tag.get_text(strip=True).lower()
            match = re.search(r'(\d{1,2})\s+(\w+)\s+(\d{4})', d_text)
            if match:
                day, mon_id, year = match.groups()
                mon_en = month_map.get(mon_id, mon_id)
                pub_date = datetime.strptime(f"{day} {mon_en} {year}", "%d %B %Y")

        articles.append({
            'title': title,
            'link': link,
            'desc': desc,
            'img': img_url,
            'date': pub_date
        })
    except Exception as e:
        print(f"Skip satu item karena error: {e}")

if not articles:
    print("Waduh, masih kosong! Cek lagi class 'news-card' di website aslinya.")
    # Debug: Print sedikit isi HTML biar kita tau isinya apa
    print(soup.prettify()[:500])
    exit()

# Generate RSS
fg = FeedGenerator()
fg.title("Kemenhaj RI News Feed")
fg.link(href=url, rel='alternate')
fg.description("Berita terkini Kementerian Haji dan Umrah RI")

for a in articles:
    fe = fg.add_entry()
    fe.title(a['title'])
    fe.link(href=a['link'])
    fe.description(a['desc'])
    if a['date']:
        # RSS butuh timezone, kita kasih UTC+7
        fe.pubDate(a['date'].replace(tzinfo=datetime.now().astimezone().tzinfo))
    if a['img']:
        fe.enclosure(url=a['img'], length=0, type='image/jpeg')

with open('output.xml', 'wb') as f:
    f.write(fg.rss_str(pretty=True))

print(f"Berhasil! {len(articles)} berita masuk ke output.xml")
