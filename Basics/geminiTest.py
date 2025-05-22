import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import random

EBAY_SOLD_SEARCH_URL = "https://www.ebay.com/sch/i.html?_nkw=laptop&_sacat=0&LH_Sold=1&LH_Complete=1"
MAX_RETRIES = 3

def init_driver():
    options = Options()
    # options.add_argument("--headless=new")  # Uncomment this after testing
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")

    # User agent for more human-like requests
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.1 Safari/605.1.15"
    ]
    options.add_argument(f"user-agent={random.choice(user_agents)}")

    options.add_argument("--log-level=3")
    options.add_experimental_option('excludeSwitches', ['enable-logging'])

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    return driver

def scrape_search_results(driver, search_url):
    print(f"\n[i] Navigating to search results: {search_url}")
    items_data = []

    try:
        driver.get(search_url)
        time.sleep(5)

        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(3)

        wait = WebDriverWait(driver, 25)
        wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".s-item")))
        item_elements = driver.find_elements(By.CSS_SELECTOR, ".s-item")

        if not item_elements:
            print("[!] No items found.")
            return []

        for item_elem in item_elements:
            item_data = {
                "title": None, "price": None, "condition": None,
                "sold_on": None, "shipping": None, "link": None,
                "specifications": {}
            }

            try:
                title_link_elem = item_elem.find_element(By.CSS_SELECTOR, 'a.s-item__link')
                item_data["title"] = title_link_elem.text.strip()
                item_data["link"] = title_link_elem.get_attribute('href')
            except NoSuchElementException:
                continue

            if not item_data["link"] or "ebay.com/itm/" not in item_data["link"]:
                continue

            try:
                item_data["price"] = item_elem.find_element(By.CSS_SELECTOR, '.s-item__price').text.strip()
            except NoSuchElementException:
                item_data["price"] = "N/A"

            try:
                item_data["condition"] = item_elem.find_element(By.CSS_SELECTOR, '.SECONDARY_INFO').text.strip()
            except NoSuchElementException:
                item_data["condition"] = "N/A"

            try:
                item_data["sold_on"] = item_elem.find_element(By.CSS_SELECTOR, '.s-item__title--tagblock').text.strip()
            except NoSuchElementException:
                item_data["sold_on"] = "N/A"

            try:
                item_data["shipping"] = item_elem.find_element(By.CSS_SELECTOR, '.s-item__shipping').text.strip()
            except NoSuchElementException:
                item_data["shipping"] = "N/A"

            print(f"  ✓ Found: {item_data['title']} - {item_data['price']}")
            items_data.append(item_data)

        print(f"[✓] Total items scraped from listing: {len(items_data)}")
        return items_data

    except Exception as e:
        print(f"[!] Error while scraping: {e}")
        return []

def scrape_item_full_details(driver, url):
    try:
        driver.get(url)
        time.sleep(4)
        wait = WebDriverWait(driver, 15)
        wait.until(EC.presence_of_element_located((By.ID, 'itemTitle')))

        specs = {}
        spec_rows = driver.find_elements(By.CSS_SELECTOR, 'div.itemAttr table tr')
        for row in spec_rows:
            cells = row.find_elements(By.TAG_NAME, 'td')
            for i in range(0, len(cells) - 1, 2):
                key = cells[i].text.strip().replace(":", "")
                value = cells[i+1].text.strip()
                if key:
                    specs[key] = value
        return specs

    except TimeoutException:
        print("[!] Timeout loading item page.")
        return None
    except Exception as e:
        print(f"[!] Error scraping item details: {e}")
        return None

def main():
    final_scraped_results = []
    driver = init_driver()

    if not driver:
        print("[x] Failed to initialize driver.")
        return

    try:
        items = scrape_search_results(driver, EBAY_SOLD_SEARCH_URL)

        if not items:
            print("[!] No items found!")
            return

        print("\n--- Scraping individual item pages ---")
        for item in items[:5]:  # Scrape details for first 5 items only
            url = item["link"]
            for attempt in range(1, MAX_RETRIES + 1):
                print(f"\nScraping ({attempt}/{MAX_RETRIES}): {item['title']}")
                specs = scrape_item_full_details(driver, url)
                if specs is not None:
                    item["specifications"] = specs
                    break
                time.sleep(5)
            final_scraped_results.append(item)

    finally:
        driver.quit()

    print("\n--- Final Results ---")
    for item in final_scraped_results:
        print(f"Title: {item['title']}")
        print(f"Price: {item['price']}")
        print(f"Condition: {item['condition']}")
        print(f"Sold On: {item['sold_on']}")
        print(f"Shipping: {item['shipping']}")
        print(f"Link: {item['link']}")
        if item['specifications']:
            for k, v in item['specifications'].items():
                print(f"  {k}: {v}")
        else:
            print("  No specifications found.")
        print("=" * 40)

if __name__ == "__main__":
    main()
