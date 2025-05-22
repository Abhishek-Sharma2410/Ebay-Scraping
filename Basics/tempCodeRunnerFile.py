from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import time

# Setup headless Chrome
options = Options()
options.add_argument("--headless")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()),
options=options)

# eBay sold items link
url = "https://www.ebay.com/sch/i.html?_nkw=automobile+parts&_sacat=0&_from=R40&_trksid=m570.l1313"

driver.get(url)
time.sleep(3)
soup = BeautifulSoup(driver.page_source, 'html.parser')
items = soup.select('.s-item')
results = []

def scrape_item_details(item_url):
    """Scrapes the specifications from a single item's page."""
    try:
        driver.get(item_url)
        time.sleep(2)  # Give the page time to load
        item_soup = BeautifulSoup(driver.page_source, 'html.parser')
        specifications = {}
        item_specifics_table = item_soup.select_one('.ux-layout-section__item--table')
        if item_specifics_table:
            rows = item_specifics_table.select('tr')
            for row in rows:
                header = row.select_one('.ux-labels-values__labels')
                value = row.select_one('.ux-labels-values__values')
                if header and value:
                    specifications[header.text.strip(':')] = value.text.strip()
        return specifications
    except Exception as e:
        print(f"Error scraping details from {item_url}: {e}")
        return {}

for item in items:
    title_element = item.select_one('.s-item__title')
    new_link = item.select_one('a.s-item__link')
    price_element = item.select_one('.s-item__price')
    status_element = item.select_one('.SECONDARY_INFO')
    sold_date_element = item.select_one('.s-item__caption--row .POSITIVE')
    shipping_element = item.select_one('.s-item__shipping, .s-item__freeXDays')
    item_link = title_element['href'] if title_element and 'href' in title_element.attrs else None
    new_link_href = new_link['href'] if new_link and 'href' in new_link.attrs else None

    item_data = {
        "title": title_element.text if title_element else None,
        "price": price_element.text if price_element else None,
        "condition": status_element.text if status_element else None,
        "sold_on": sold_date_element.text if sold_date_element else None,
        "shipping": shipping_element.text if shipping_element else None,
        "link": item_link,
        "newLink": new_link_href,
        "specifications": {}  # Initialize an empty dictionary for specifications
    }

    if item_link:
        item_data["specifications"] = scrape_item_details(item_link)

    results.append(item_data)

driver.quit()

# Display the scraped items with specifications
for r in results:
    print(r)