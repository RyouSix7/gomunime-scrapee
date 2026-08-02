# > kiro - Gomunime Full Scraper (Playwright + Delay)
import asyncio
import json
import re
import random
from datetime import datetime
from playwright.async_api import async_playwright

BASE_URL = "https://gomunime.top/"
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

# === KONFIGURASI DELAY ===
MIN_DELAY = 1.0   # detik
MAX_DELAY = 3.0   # detik
SCROLL_DELAY = 0.5

async def random_delay():
    """Tidur dengan durasi acak antara MIN_DELAY dan MAX_DELAY"""
    delay = random.uniform(MIN_DELAY, MAX_DELAY)
    await asyncio.sleep(delay)

async def scrape_page(url, selector, max_items=50):
    """Scrape halaman dengan selector tertentu, dilengkapi delay"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(url, wait_until='networkidle')
        await random_delay()  # Delay awal

        # Scroll pelan-pelan dengan delay
        for i in range(4):
            await page.mouse.wheel(0, 800 + random.randint(0, 400))
            await asyncio.sleep(SCROLL_DELAY + random.uniform(0.1, 0.5))
        
        # Ambil elemen
        items = await page.query_selector_all(selector)
        result = []
        for idx, item in enumerate(items[:max_items]):
            text = await item.inner_text()
            link = await item.get_attribute('href')
            if link:
                if not link.startswith('http'):
                    link = BASE_URL + link.lstrip('/')
                result.append({
                    'title': text.strip() or 'Unknown',
                    'url': link
                })
            # Delay antar item biar gak overload
            if idx % 5 == 0:
                await asyncio.sleep(random.uniform(0.2, 0.6))
        
        await browser.close()
        return result

async def scrape_status_page(status_type):
    """Scrape halaman status (ongoing/completed) dengan delay"""
    url = f"{BASE_URL}status/{status_type}"
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(url, wait_until='networkidle')
        await random_delay()

        # Scroll bertahap dengan delay
        for _ in range(6):
            await page.mouse.wheel(0, 1200 + random.randint(0, 600))
            await asyncio.sleep(SCROLL_DELAY + random.uniform(0.2, 0.7))
        
        # Ambil semua link anime
        anime_links = await page.query_selector_all('a[href*="/anime/"]')
        result = []
        seen = set()
        for idx, link in enumerate(anime_links):
            href = await link.get_attribute('href')
            text = await link.inner_text()
            if href and href not in seen and text.strip():
                seen.add(href)
                if not href.startswith('http'):
                    href = BASE_URL + href.lstrip('/')
                result.append({
                    'title': text.strip(),
                    'url': href
                })
            # Delay setiap 10 item
            if idx % 10 == 0:
                await asyncio.sleep(random.uniform(0.3, 0.8))
        
        await browser.close()
        return result

async def scrape_homepage():
    """Scrape homepage dengan delay"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(BASE_URL, wait_until='networkidle')
        await random_delay()

        # Scroll pelan
        for _ in range(3):
            await page.mouse.wheel(0, 800 + random.randint(0, 300))
            await asyncio.sleep(SCROLL_DELAY + random.uniform(0.1, 0.4))
        
        # Episode terbaru
        latest = []
        ep_links = await page.query_selector_all('a[href*="/episode/"]')
        for idx, link in enumerate(ep_links[:20]):
            href = await link.get_attribute('href')
            text = await link.inner_text()
            if href:
                if not href.startswith('http'):
                    href = BASE_URL + href.lstrip('/')
                latest.append({
                    'title': text.strip() or 'Episode',
                    'url': href
                })
            if idx % 5 == 0:
                await asyncio.sleep(random.uniform(0.1, 0.3))
        
        # Genre
        genres = []
        genre_links = await page.query_selector_all('a[href*="/genre/"]')
        seen_genre = set()
        for idx, link in enumerate(genre_links):
            href = await link.get_attribute('href')
            text = await link.inner_text()
            if href and text.strip() and text.strip() not in seen_genre:
                seen_genre.add(text.strip())
                if not href.startswith('http'):
                    href = BASE_URL + href.lstrip('/')
                genres.append({
                    'name': text.strip(),
                    'url': href
                })
            if idx % 10 == 0:
                await asyncio.sleep(random.uniform(0.1, 0.3))
        
        # Ambil info total series dari meta
        total_series = 487
        desc = await page.query_selector('meta[name="description"]')
        if desc:
            content = await desc.get_attribute('content')
            if content:
                numbers = re.findall(r'\d+', content)
                if numbers:
                    total_series = int(numbers[0])
        
        await browser.close()
        return {
            'latest_episodes': latest,
            'genres': genres[:15],
            'total_series': total_series
        }

async def main():
    print("[+] Scraping homepage...")
    homepage = await scrape_homepage()
    await random_delay()
    
    print("[+] Scraping ongoing anime...")
    ongoing = await scrape_status_page('ongoing')
    await random_delay()
    
    print("[+] Scraping completed anime...")
    completed = await scrape_status_page('completed')
    
    # Top anime dari episode terbaru
    top = homepage['latest_episodes'][:10]
    
    result = {
        'timestamp': datetime.now().isoformat(),
        'source': BASE_URL,
        'summary': {
            'total_series': homepage['total_series'],
            'ongoing_count': len(ongoing),
            'completed_count': len(completed)
        },
        'latest_episodes': homepage['latest_episodes'],
        'genres': homepage['genres'],
        'ongoing': ongoing[:50],
        'completed': completed[:50],
        'top_anime': top
    }
    
    with open('data.json', 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Done! {len(ongoing)} ongoing, {len(completed)} completed")

if __name__ == '__main__':
    asyncio.run(main())
