from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
from datetime import datetime, timezone
import time

def scrape_kemenhaj():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        # Buka satu page buat list berita
        page = browser.new_page()
        
        url = "https://haji.go.id/berita"
        print(f"Membuka {url}...")
        
        try:
            page.goto(url, wait_until="networkidle")
            page.wait_for_selector(".news-card", timeout=20000)
            time.sleep(2)
        except Exception as e:
            print(f"Gagal loading halaman utama: {e}")
            browser.close()
            return []

        html_content = page.content()
        soup = BeautifulSoup(html_content, 'html.parser')
        
        articles = []
        # Batasi ambil 5 berita terbaru biar gak kelamaan pas deep scraping
        cards = soup.find_all('div', class_='news-card')[:5] 
        
        for card in cards:
            title_el = card.find('h3', class_='news-card-title')
            link_el = card.find('a', class_='news-card-title-link')
            img_el = card.find('img')

            if title_el and link_el:
                link = link_el['href']
                full_link = f"https://haji.go.id{link}" if link.startswith('/') else link
                
                # Setup Link Gambar
                img_url = None
                if img_el and img_el.get('src'):
                    src = img_el['src']
                    img_url = f"https://haji.go.id{src}" if src.startswith('/') else src

                # --- DEEP SCRAPING: Buka halaman detail untuk ambil isi lengkap ---
                print(f"Mengambil isi lengkap: {title_el.get_text(strip=True)}...")
                detail_page = browser.new_page()
                try:
                    detail_page.goto(full_link, wait_until="networkidle")
                    # Selector .news-detail-content biasanya buat isi berita di portal pemerintah
                    # Jika tidak muncul, kita fallback ke teks card awal
                    content_el = detail_page.query_selector(".news-detail-content")
                    if content_el:
                        full_text = content_el.inner_text().strip()
                    else:
                        full_text = "Isi detail tidak ditemukan di halaman."
                except:
                    full_text = "Gagal memuat detail berita."
                finally:
                    detail_page.close()

                articles.append({
                    'title': title_el.get_text(strip=True),
                    'link': full_link,
                    'content': full_text,
                    'image': img_url
                })
        
        browser.close()
        return articles

# --- Generate RSS ---

data_berita = scrape_kemenhaj()

if data_berita:
    fg = FeedGenerator()
    fg.title("Kemenhaj RI News Feed")
    # Alternate link ke web asli
    fg.link(href="https://haji.go.id/berita", rel='alternate')
    # Self link biar dapet skor validasi sempurna
    fg.link(href="https://raw.githubusercontent.com/sukalaper/himpuh-rss/main/output.xml", rel='self')
    fg.description("Berita utuh tanpa kepotong dari Kementerian Haji dan Umrah RI")
    fg.language('id')
    fg.lastBuildDate(datetime.now(timezone.utc))

    for item in data_berita:
        entry = fg.add_entry()
        entry.title(item['title'])
        entry.link(href=item['link'])
        # Pake GUID biar RSS Reader gak bingung
        entry.guid(item['link'], permalink=True)
        # Masukkan konten utuh ke description
        entry.description(item['content'])
        
        if item['image']:
            entry.enclosure(url=item['image'], length='0', type='image/jpeg')
        
        entry.pubDate(datetime.now(timezone.utc))

    try:
        rss_feed = fg.rss_str(pretty=True)
        with open('output.xml', 'wb') as f:
            f.write(rss_feed)
        print(f"Selesai! {len(data_berita)} berita lengkap masuk ke output.xml.")
    except Exception as e:
        print(f"Gagal nulis file: {e}")
else:
    print("Gak ada data yang diambil der.")
    
