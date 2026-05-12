from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
from datetime import datetime, timezone
import time

def scrape_kemenhaj():
    with sync_playwright() as p:
        # Launch browser
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        url = "https://haji.go.id/berita"
        print(f"Membuka {url}...")
        
        try:
            # Go to URL and wait for the content to load
            page.goto(url, wait_until="networkidle")
            # Tunggu selector spesifik card berita muncul
            page.wait_for_selector(".news-card", timeout=20000)
            time.sleep(2) # Kasih nafas dikit buat render sempurna
        except Exception as e:
            print(f"Waduh, ada masalah pas loading: {e}")
            browser.close()
            return []

        html_content = page.content()
        soup = BeautifulSoup(html_content, 'html.parser')
        browser.close()

        articles = []
        cards = soup.find_all('div', class_='news-card')
        
        for card in cards:
            title_el = card.find('h3', class_='news-card-title')
            link_el = card.find('a', class_='news-card-title-link')
            excerpt_el = card.find('p', class_='news-card-excerpt')
            img_el = card.find('img')

            if title_el and link_el:
                link = link_el['href']
                # Pastiin link berita absolut
                full_link = f"https://haji.go.id{link}" if link.startswith('/') else link
                
                # Pastiin link gambar absolut
                img_url = None
                if img_el and img_el.get('src'):
                    src = img_el['src']
                    img_url = f"https://haji.go.id{src}" if src.startswith('/') else src

                articles.append({
                    'title': title_el.get_text(strip=True),
                    'link': full_link,
                    'excerpt': excerpt_el.get_text(strip=True) if excerpt_el else "",
                    'image': img_url
                })
        return articles

# --- Eksekusi ---

data_berita = scrape_kemenhaj()

if data_berita:
    fg = FeedGenerator()
    fg.title("Kemenhaj RI News Feed")
    fg.link(href="https://haji.go.id/berita", rel='alternate')
    fg.description("Berita terkini dari Kementerian Haji dan Umrah RI")
    fg.language('id')

    for item in data_berita:
        entry = fg.add_entry()
        entry.title(item['title'])
        entry.link(href=item['link'])
        entry.description(item['excerpt'])
        
        # Tambahin gambar sebagai enclosure kalau ada
        if item['image']:
            # Kita set length=0 karena kita gak tau size filenya secara dinamis
            entry.enclosure(url=item['image'], length='0', type='image/jpeg')
        
        # Set pubDate ke waktu sekarang (karena scraping biasanya buat berita terbaru)
        entry.pubDate(datetime.now(timezone.utc))

    # Proses simpan file
    try:
        # Gunakan fg.rss_str() untuk dapetin full XML content
        rss_feed = fg.rss_str(pretty=True)
        with open('output.xml', 'wb') as f:
            f.write(rss_feed)
        print(f"Selesai! {len(data_berita)} berita berhasil masuk ke output.xml.")
    except Exception as e:
        print(f"Gagal pas mau nulis file: {e}")
else:
    print("Gak ada data berita yang berhasil diambil der.")
