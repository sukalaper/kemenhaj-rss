from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
from datetime import datetime, timezone
import time

def scrape_kemenhaj():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        page = context.new_page()
        
        url = "https://haji.go.id/berita"
        print(f"Membuka {url}...")
        
        try:
            page.goto(url, wait_until="networkidle", timeout=60000)
            page.wait_for_selector(".news-card", timeout=20000)
            time.sleep(2)
        except Exception as e:
            print(f"Gagal loading halaman utama: {e}")
            browser.close()
            return []

        html_content = page.content()
        soup = BeautifulSoup(html_content, 'html.parser')
        
        articles = []
        cards = soup.find_all('div', class_='news-card')[:5] 
        
        for card in cards:
            title_el = card.find('h3', class_='news-card-title')
            link_el = card.find('a', class_='news-card-title-link')
            img_el = card.find('img')

            if title_el and link_el:
                title_text = title_el.get_text(strip=True)
                link = link_el['href']
                full_link = f"https://haji.go.id{link}" if link.startswith('/') else link
                
                img_url = None
                if img_el and img_el.get('src'):
                    src = img_el['src']
                    img_url = f"https://haji.go.id{src}" if src.startswith('/') else src

                print(f"Mengambil konten utuh: {title_text}")
                detail_page = context.new_page()
                full_html_content = ""
                try:
                    detail_page.goto(full_link, wait_until="domcontentloaded", timeout=30000)
                    
                    detail_page.wait_for_selector(".news-detail-content, .field--name-body", timeout=5000)
                    
                    content_element = detail_page.query_selector(".news-detail-content") or \
                                      detail_page.query_selector(".field--name-body") or \
                                      detail_page.query_selector("article")
                    
                    if content_element:
                        full_html_content = content_element.inner_html()
                    else:
                        paragraphs = detail_page.query_selector_all("p")
                        full_html_content = "".join([f"<p>{p.inner_text()}</p>" for p in paragraphs if len(p.inner_text()) > 50])
                except Exception as e:
                    print(f"Gagal ambil detail {title_text}: {e}")
                    full_html_content = "<p>Gagal memuat detail berita utuh.</p>"
                finally:
                    detail_page.close()

                articles.append({
                    'title': title_text,
                    'link': full_link,
                    'content': full_html_content,
                    'image': img_url
                })
        
        browser.close()
        return articles

data_berita = scrape_kemenhaj()

if data_berita:
    fg = FeedGenerator()
    fg.load_extension('content')
    
    fg.title("Kemenhaj RI News Feed")
    fg.link(href="https://haji.go.id/berita", rel='alternate')
    fg.link(href="https://raw.githubusercontent.com/sukalaper/himpuh-rss/main/output.xml", rel='self')
    fg.description("Berita utuh Kementerian Haji dan Umrah RI (Tanpa Kepotong)")
    fg.language('id')
    fg.lastBuildDate(datetime.now(timezone.utc))

    for item in data_berita:
        entry = fg.add_entry()
        entry.title(item['title'])
        entry.link(href=item['link'])
        entry.guid(item['link'], permalink=True)
        
        entry.content(item['content'], type='CDATA')
        
        soup_clear = BeautifulSoup(item['content'], "html.parser")
        entry.description(soup_clear.get_text(separator="\n")[:300] + "...")
        
        if item['image']:
            entry.enclosure(url=item['image'], length='0', type='image/jpeg')
        
        entry.pubDate(datetime.now(timezone.utc))

    try:
        rss_feed = fg.rss_str(pretty=True)
        with open('output.xml', 'wb') as f:
            f.write(rss_feed)
        print(f"\nSelesai der! {len(data_berita)} berita sudah lebih rapi di output.xml.")
    except Exception as e:
        print(f"Gagal nulis file: {e}")
else:
    print("Gak ada berita yang bisa diambil.")
