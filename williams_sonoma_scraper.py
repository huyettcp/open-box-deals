import json
import logging
import random
import time
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

URL = "https://www.williams-sonoma.com/shop/sale-special-offer/open-box-deals/"

options = uc.ChromeOptions()
options.add_argument("--no-sandbox")
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_argument("--window-size=1920,1080")
options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36")

driver = uc.Chrome(options=options)
wait = WebDriverWait(driver, 20)

def slow_human_scroll(max_scrolls=40):
    logging.info("Starting human-like scrolling...")
    time.sleep(5)  # initial wait for page JS to settle

    for scroll_num in range(max_scrolls):
        driver.execute_script("window.scrollBy(0, window.innerHeight * 0.8);")
        logging.info(f"Scroll {scroll_num + 1}/{max_scrolls}")
        time.sleep(random.uniform(1, 2))

        try:
            show_more = driver.find_element(By.XPATH, "//div[contains(@class, 'buttons') and contains(@class, 'show-me-more')]/button")
            if show_more.is_displayed():
                logging.info("Clicking 'Show Me More' button")
                driver.execute_script("arguments[0].click();", show_more)
                time.sleep(random.uniform(2.5, 3.5))
        except:
            continue  # No button visible, continue scrolling

def extract_product_info(product):
    try:
        title_elem = product.find_element(By.CLASS_NAME, "product-name")
        title = title_elem.text.strip()

        link = product.find_element(By.CSS_SELECTOR, "a.product-image-link").get_attribute("href")
        full_url = f"https://www.williams-sonoma.com{link}" if link.startswith("/") else link

        try:
            orig_price = product.find_element(By.CLASS_NAME, "suggested-price").text.strip()
        except:
            orig_price = None

        try:
            sale_price = product.find_element(By.CLASS_NAME, "sale-price").text.strip()
        except:
            sale_price = None

        # Scroll into view to help load image
        try:
            ActionChains(driver).move_to_element(product).perform()
            time.sleep(1.5)
        except:
            pass

        image_url = None
        try:
            image_elem = product.find_element(By.CSS_SELECTOR, "img.product-image")
        except:
            try:
                image_elem = product.find_element(By.CSS_SELECTOR, "img.alt-image")
            except:
                logging.warning("No image found for product.")
                image_elem = None

        if image_elem:
            image_url = image_elem.get_attribute("src") or image_elem.get_attribute("data-src")
            if image_url:
                image_url = image_url.replace("-t.jpg", "-c.jpg").replace("-j.jpg", "-c.jpg")

        return {
            "Product Name": title,
            "Original Price": orig_price,
            "Sale Price": sale_price,
            "Image URL": image_url,
            "Product Display Page URL": full_url,
            "Store": "Williams Sonoma"
        }

    except Exception as e:
        logging.warning(f"Failed to parse product: {e}")
        return None

def main():
    try:
        logging.info(f"Opening {URL}")
        driver.get(URL)
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))

        slow_human_scroll()

        with open("page_debug_dump.html", "w") as f:
            f.write(driver.page_source)
        logging.info("Saved page HTML to page_debug_dump.html")

        products = driver.find_elements(By.CLASS_NAME, "grid-item")
        logging.info(f"Found {len(products)} product elements")

        results = []
        for product in products:
            info = extract_product_info(product)
            if info:
                results.append(info)

        with open("williams_sonoma_open_box.json", "w") as f:
            json.dump(results, f, indent=2)
        logging.info(f"Saved {len(results)} products to JSON")

    except Exception as e:
        logging.error(f"Unhandled scraping error: {e}")
        with open("failed_dump.html", "w") as f:
            f.write(driver.page_source)
        logging.info("Saved HTML dump to failed_dump.html")

    finally:
        driver.quit()

if __name__ == "__main__":
    main()