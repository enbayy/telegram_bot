import random
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import requests
import time
import re

def amazon_urunleri(url, chromedriver_yolu, max_urun=10):
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--lang=tr-TR")
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')

    service = Service(chromedriver_yolu)
    driver = webdriver.Chrome(service=service, options=options)

    driver.get(url)
    time.sleep(3)

    urun_listesi = []

    try:
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.s-main-slot"))
        )
        urunler = driver.find_elements(By.CSS_SELECTOR, "div.s-main-slot > div[data-component-type='s-search-result']")
        if not urunler:
            driver.quit()
            print("Amazon ürün listesi boş.")
            return []

        random.shuffle(urunler)

        for urun in urunler[:max_urun]:
            try:
                baslik = urun.find_element(By.CSS_SELECTOR, "h2 span").text.strip()
            except:
                baslik = "Başlık yok"

            uzun_link = ""
            try:
                a_tag = urun.find_element(By.CSS_SELECTOR, "h2 a")
                href = a_tag.get_attribute("href")
                if href:
                    uzun_link = href.strip()
            except:
                uzun_link = ""

            if not uzun_link:
                urun_id = urun.get_attribute("data-asin")
                if urun_id:
                    uzun_link = f"https://www.amazon.com.tr/dp/{urun_id}"

            urun_id = None
            if uzun_link:
                match = re.search(r"/dp/([A-Z0-9]{10})", uzun_link)
                if match:
                    urun_id = match.group(1)

            if urun_id:
                link = f"https://www.amazon.com.tr/dp/{urun_id}"
            elif uzun_link:
                link = uzun_link
            else:
                link = "Link bulunamadı"

            fiyat = "Fiyat yok"
            try:
                fiyat_tam = urun.find_element(By.CSS_SELECTOR, "span.a-price-whole").text.strip()
                fiyat_kurus = urun.find_element(By.CSS_SELECTOR, "span.a-price-fraction").text.strip()
                fiyat = f"{fiyat_tam},{fiyat_kurus} TL"
            except:
                try:
                    fiyat = urun.find_element(By.CSS_SELECTOR, "span.a-price > span.a-offscreen").text.strip()
                except:
                    fiyat = "Fiyat yok"

            urun_listesi.append({
                "baslik": baslik,
                "link": link,
                "fiyat": fiyat
            })

    except Exception as e:
        print("Hata oluştu:", e)
        driver.quit()
        return []

    driver.quit()
    return urun_listesi


def telegram_gonder(token, chat_id, mesaj, max_length=4000):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    mesajlar = [mesaj[i:i+max_length] for i in range(0, len(mesaj), max_length)]

    for parca in mesajlar:
        data = {
            "chat_id": chat_id,
            "text": parca,
            "parse_mode": "HTML"
        }
        response = requests.post(url, data=data)
        if not response.ok:
            print("Telegram gönderim hatası:", response.text)
            return response.json()

    return {"ok": True, "description": "Tüm mesajlar gönderildi."}


if __name__ == "__main__":
    chromedriver_yolu = r"C:\chromedriver-win64\chromedriver.exe"  # chromedriver yolunu kendine göre değiştir

    kategori_listesi = [
        "telefon", "tablet", "kulaklık", "kamera", "bilgisayar", "oyun-konsolu", "akıllı-saat", "ev-aksesuarları"
    ]

    toplam_urun_sayisi = 10
    urunler_tumu = []

    # Kategorilerden karışık ürün toplamak için:
    # Her kategoriden max 3 ürün çekelim, toplam 10 ürün olacak şekilde sınırla
    max_urun_kategori = 3

    for kategori in kategori_listesi:
        url = f"https://www.amazon.com.tr/s?k={kategori}"
        urunler = amazon_urunleri(url, chromedriver_yolu, max_urun=max_urun_kategori)
        urunler_tumu.extend(urunler)
        if len(urunler_tumu) >= toplam_urun_sayisi:
            break

    # Toplam ürün sayısını 10'a indiriyoruz (fazlalık varsa)
    urunler_tumu = urunler_tumu[:toplam_urun_sayisi]

    if urunler_tumu:
        mesaj = ""
        for index, urun in enumerate(urunler_tumu, 1):
            mesaj += f"<b>Ürün {index}:</b>\n"
            mesaj += f"<b>Başlık:</b> {urun['baslik']}\n"
            mesaj += f"<b>Fiyat:</b> {urun['fiyat']}\n"
            mesaj += f"<b>Link:</b> {urun['link']}\n\n"

        token = "8416847183:AAFaskljy6TjiPIOQR20vyrhGcC3njC80nQ"
        chat_ids = ["1118080116", "5258679254"]

        for chat_id in chat_ids:
            sonuc = telegram_gonder(token, chat_id, mesaj)
            print(f"Chat ID {chat_id} için gönderim sonucu:", sonuc)
    else:
        print("Ürün çekilemedi.")