import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
from typing import Dict, List
import re
import time

class TrackerScraper:
    def __init__(self):
        self.site_url = "https://opentrackers.org/tag/limited-signup/"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1"
        }
        self.session = requests.Session()

    def temizle_metin(self, metin: str) -> str:
        if not metin:
            return ""
        metin = re.sub(r'\s+', ' ', metin)
        return metin.strip()

    def url_duzenle(self, url: str) -> str:
        if not url:
            return ""
        if not url.startswith('http'):
            return f"https://opentrackers.org{url}"
        return url

    def sayfa_icerik_al(self) -> str:
        try:
            # Session kullan ve birkaç deneme yap
            for _ in range(3):
                response = self.session.get(
                    self.site_url,
                    headers=self.headers,
                    timeout=30
                )
                if response.status_code == 200:
                    return response.text
                time.sleep(2)  # Her denemeden önce bekle
            return ""
        except Exception as e:
            print(f"Bağlantı hatası: {e}")
            return ""

    def veri_ayikla(self) -> List[Dict[str, str]]:
        html_content = self.sayfa_icerik_al()
        if not html_content:
            return []

        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            veriler = []

            # Farklı class isimleri dene
            post_containers = (
                soup.find_all("article") or 
                soup.find_all("div", class_=lambda x: x and ('post' in x.lower())) or
                soup.find_all("div", class_="post-list")
            )

            if not post_containers:
                print("HTML içeriği:")
                print(html_content[:500])  # İlk 500 karakteri göster
                return []

            for post in post_containers:
                try:
                    # Başlık bulmak için farklı yöntemler
                    title = None
                    for title_tag in ['h1', 'h2', 'h3']:
                        title_elem = post.find(title_tag)
                        if title_elem:
                            title = title_elem.text
                            break
                    
                    if not title:
                        continue

                    # Link bulmak için farklı yöntemler
                    link = None
                    link_elem = post.find('a')
                    if link_elem:
                        link = link_elem.get('href')

                    if not link:
                        continue

                    # Tarih bulmak için farklı yöntemler
                    date = None
                    date_elem = (
                        post.find('time') or
                        post.find(class_=lambda x: x and 'date' in x.lower())
                    )
                    
                    if date_elem:
                        date = date_elem.get('datetime') or date_elem.text
                    else:
                        date = datetime.now().strftime("%Y-%m-%d")

                    # İçerik özeti
                    content = ""
                    content_elem = (
                        post.find(class_='entry-content') or
                        post.find(class_='content') or
                        post.find('p')
                    )
                    
                    if content_elem:
                        content = self.temizle_metin(content_elem.text)

                    veri = {
                        "baslik": self.temizle_metin(title),
                        "baglanti": self.url_duzenle(link),
                        "tarih": self.temizle_metin(date),
                        "ozet": content[:200] + "..." if content else "",
                        "zaman": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                    veriler.append(veri)

                except Exception as e:
                    print(f"Post işlenirken hata: {e}")
                    continue

            return sorted(veriler, key=lambda x: x['tarih'], reverse=True)

        except Exception as e:
            print(f"HTML parse hatası: {e}")
            return []

def main() -> None:
    try:
        print("Veriler çekiliyor...")
        scraper = TrackerScraper()
        veriler = scraper.veri_ayikla()
        
        if veriler:
            with open("tracker_data.json", "w", encoding="utf-8") as f:
                json.dump(veriler, f, ensure_ascii=False, indent=2)
            
            print(f"\n{'='*50}")
            print(f"Toplam {len(veriler)} tracker bulundu")
            print(f"{'='*50}\n")
            
            for veri in veriler:
                print(f"📌 {veri['baslik']}")
                print(f"🔗 {veri['baglanti']}")
                print(f"📅 {veri['tarih']}")
                if veri['ozet']:
                    print(f"📝 {veri['ozet']}")
                print(f"{'-'*50}\n")
        else:
            print("\n❌ Veri bulunamadı.")
            print("Lütfen site yapısını kontrol edin veya daha sonra tekrar deneyin.")
            
    except Exception as e:
        print(f"\n❌ Program hatası: {e}")
        raise

if __name__ == "__main__":
    main()
