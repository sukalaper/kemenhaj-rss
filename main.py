import asyncio
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
from datetime import datetime
import re

def scrape():
    with sync_playwright() as p:
        # Buka browser
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        # Buka URL
        print("Membuka haji.go.id/berita...")
        page.goto("https://haji.go.id/berita", wait_until="networkidle")
        
        # TUNGGUIN sampe news-card muncul (kunci utamanya di sini)
        try:
            page.wait_for_selector(".news-card", timeout=15000)
        except:
            print("Timeout: Berita gak muncul-muncul.")
            browser.close()
            return []

        # Ambil HTML yang udah ke-render
        content = page.content()
        soup = BeautifulSoup(content, 'html.parser')
        browser.close()
        
        # Parsing pake BeautifulSoup kayak biasa
        articles = []
        news_cards = soup.find_all('div', class_='news-card')
        
        for card in news_cards:
            title_el = card.find('h3', class_='news-card-title')
            link_el = card.find('a', class_='news-card-title-link')
            excerpt_el = card.find('p', class_='news-card-excerpt')
            img_el = card.find('img')
            
            if title_el and link_el:
                link = link_el['href']
                articles.append({
                    'title': title_el.get_text(strip=True),
                    'link': f"https://haji.go.id{link}" if link.startswith('/') else link,
                    'desc': excerpt_el.get_text(strip=True) if excerpt_el else "",
                    'img': img_el['src'] if img_el else None
                })
        return articles

# Jalanin Scraper
articles = scrape()

if articles:
    fg = FeedGenerator()
    fg.title("Kemenhaj RI News Feed")
    fg.link(href="https://haji.go.id/berita", rel='alternate')
    fg.description("Berita terkini Kementerian Haji dan Umrah RI")

    for a in articles:
        fe = fg.add_entry()
        fe.title(a['title'])
        fe.link(href=a['link'])
        fe.description(a['desc'])
        if a['img']:
            fe.enclosure(url=a['img'], length=0, type='image/jpeg')
        fe.pubDate(datetime.now().astimezone())

    with open('output.xml', 'wb') as f:
        f.write(fg.rss_str(pretty=True))
    print(f"Update Selesai! {len(articles)} berita masuk.")
else:
    print("Gagal dapetin berita.")
