import requests
import json
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
from datetime import datetime

url = "https://haji.go.id/berita"
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
}

response = requests.get(url, headers=headers, timeout=20)
soup = BeautifulSoup(response.text, 'html.parser')

articles = []

# Trik: Cari data di dalam script __NEXT_DATA__ (Standar Next.js/React)
next_data = soup.find('script', id='__NEXT_DATA__')

if next_data:
    # Kalau webnya Next.js, semua berita ada di sini dalam bentuk JSON
    data_json = json.loads(next_data.string)
    # Jalur data biasanya: props -> pageProps -> initialData -> berita
    # Kita cari secara rekursif atau lgsg ke intinya
    try:
        # Ini path umum, bisa beda dikit tapi biasanya ada di pageProps
        raw_news = data_json['props']['pageProps'].get('news', []) or \
                   data_json['props']['pageProps'].get('data', [])
        
        for item in raw_news[:10]:
            articles.append({
                'title': item.get('title'),
                'link': f"https://haji.go.id/berita/{item.get('slug')}",
                'desc': item.get('excerpt'),
                'date': item.get('created_at'),
                'img': item.get('image')
            })
    except:
        pass

# Kalau trik script gagal, kita balik ke BeautifulSoup biasa (cara lo)
if not articles:
    news_cards = soup.find_all('div', class_='news-card')
    for card in news_cards:
        title_tag = card.find('h3', class_='news-card-title')
        link_tag = card.find('a', href=True)
        date_tag = card.find('span', class_='news-card-date')
        
        if title_tag:
            articles.append({
                'title': title_tag.get_text(strip=True),
                'link': 'https://haji.go.id' + link_tag['href'] if link_tag['href'].startswith('/') else link_tag['href'],
                'desc': card.find('p', class_='news-card-excerpt').get_text(strip=True) if card.find('p', class_='news-card-excerpt') else "",
                'date': date_tag.get_text(strip=True) if date_tag else None,
                'img': card.find('img')['src'] if card.find('img') else None
            })

# Bikin RSS
fg = FeedGenerator()
fg.title("Kemenhaj RI News Feed")
fg.link(href=url, rel='alternate')
fg.description("Berita terkini Kementerian Haji dan Umrah RI")

for a in articles:
    fe = fg.add_entry()
    fe.title(a['title'])
    fe.link(href=a['link'])
    fe.description(a['desc'])
    # Set tanggal seadanya kalau formatnya susah di-parse
    fe.pubDate(datetime.now(timezone.utc)) 

with open('output.xml', 'wb') as f:
    f.write(fg.rss_str(pretty=True))

print(f"Update selesai! {len(articles)} berita masuk.")
