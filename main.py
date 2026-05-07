import requests
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
from datetime import datetime
import re

url = "https://haji.go.id/berita"
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'id,en-US;q=0.7,en;q=0.3',
}

try:
    # Kita coba ambil HTML mentahnya
    session = requests.Session()
    response = session.get(url, headers=headers, timeout=30)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Cari semua container berita sesuai inspect lo
    news_cards = soup.find_all('div', class_='news-card')
    
    # DEBUG: Biar keliatan di log GitHub Actions
    print(f"Jumlah news-card yang ditemukan: {len(news_cards)}")
    
    articles = []
    month_map = {
        'januari': 'January', 'februari': 'February', 'maret': 'March',
        'april': 'April', 'mei': 'May', 'juni': 'June',
        'juli': 'July', 'agustus': 'August', 'september': 'September',
        'oktober': 'October', 'november': 'November', 'desember': 'December'
    }

    for card in news_cards:
        # Judul & Link
        title_elem = card.find('h3', class_='news-card-title')
        link_elem = card.find('a', class_='news-card-title-link')
        
        if not title_elem or not link_elem:
            continue
            
        title = title_elem.text.strip()
        link = link_elem.get('href', '')
        if link.startswith('/'):
            link = 'https://haji.go.id' + link
            
        # Excerpt
        excerpt_elem = card.find('p', class_='news-card-excerpt')
        content = excerpt_elem.text.strip() if excerpt_elem else ""
        
        # Image
        img_elem = card.find('img')
        image_url = img_elem.get('src') if img_elem else None
        
        # Date
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
                except:
                    pass

        articles.append({
            'title': title,
            'link': link,
            'content': content,
            'image': image_url,
            'date': published_date
        })

    # Buat RSS
    feed = FeedGenerator()
    feed.title("Kemenhaj RI News Feed")
    feed.link(href=url, rel='alternate')
    feed.description("Berita terkini dari Kementerian Haji dan Umrah RI")

    if not articles:
        print("PERINGATAN: List artikel kosong. HTML mungkin belum ter-render.")
    else:
        for article in articles:
            entry = feed.add_entry()
            entry.title(article['title'])
            entry.content(article['content'])
            entry.link(href=article['link'])
            if article['date']:
                # Tambahin timezone manual biar RSS valid
                entry.pubDate(article['date'].replace(tzinfo=datetime.now().astimezone().tzinfo))
            if article['image']:
                entry.enclosure(url=article['image'], length=0, type='image/jpeg')

    # Update file output.xml
    with open('output.xml', 'wb') as f:
        f.write(feed.rss_str(pretty=True))

except Exception as e:
    print(f"Error sistem: {e}")
