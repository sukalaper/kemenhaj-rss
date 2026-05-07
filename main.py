from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
from datetime import datetime
import time

def scrape_kemenhaj():
    with sync_playwright() as p:
        # Launch browser gaib (headless)
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        url = "https://haji.go.id/berita"
        print(f"Membuka {url}...")
        
        # Buka halaman dan tunggu sampe koneksi anteng
        page.goto(url, wait_until="networkidle")
        
        # Trik maut: nungguin news-card muncul di HTML (max 20 detik)
        try:
            page.wait_for_selector(".news-card", timeout=20000)
            # Kasih nafas sedetik biar rendering selesai sempurna
            time.sleep(2)
        except Exception as e:
            print("Waduh, beritanya gak muncul-muncul lewat browser sekalipun.")
            browser.close()
            return []

        # Ambil HTML yang udah "mateng" (udah ke-render JS-nya)
        html_content = page.content()
        soup = BeautifulSoup(html_content, 'html.parser')
        browser.close()

        articles = []
        cards = soup.find_all('div', class_='news-card')
        
        for card in cards:
            title_el = card.find('h3', class_='news-card-title')
            link_el = card.find('a', class_='news-card-title-link')
            excerpt_el = card.find('p', class_='news-card-excerpt')
            date_el = card.find('span', class_='news-card-date')
            img_el = card.find('img')

            if title_el and link_el:
                link = link_el['href']
                articles.append({
                    'title': title_el.get_text(strip=True),
                    'link': f"https://haji.go.id{link}" if link.startswith('/') else link,
                    'excerpt': excerpt_el.get_text(strip=True) if excerpt_el else "",
                    'date': date_el.get_text(strip=True) if date_el else "",
                    'image': img_el['src'] if img_el else None
                })
        return articles

# Eksekusi Scraper
data_berita = scrape_kemenhaj()

if data_berita:
    fg = FeedGenerator()
    fg.title("Kemenhaj RI News Feed")
    fg.link(href="https://haji.go.id/berita", rel='alternate')
    fg.description("Berita terkini dari Kementerian Haji dan Umrah RI")

    for item in data_berita:
        entry = fg.add_entry()
        entry.title(item['title'])
        entry.link(href=item['link'])
        entry.description(item['excerpt'])
        if item['image']:
            entry.enclosure(url=item['image'], length=0, type='image/jpeg')
        # RSS butuh timezone, kita pake UTC+7
        entry.pubDate(datetime.now().astimezone())

    with open('output.xml', 'wb') as f:
        f.write(fg.rss_str(pretty=True))
    print(f"Mantap! {len(data_berita)} berita berhasil masuk ke output.xml")
else:
    print("Gagal dapetin data.")
