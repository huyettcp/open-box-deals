import json
import time
import random
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

logging.basicConfig(level=logging.INFO)

def dismiss_modals(driver):
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "modal_component"))
        )

        # Try known button classes across Pottery Barn / West Elm
        close_selectors = [".btnClose", ".stickyOverlayMinimizeButton"]

        for selector in close_selectors:
            buttons = driver.find_elements(By.CSS_SELECTOR, selector)
            for button in buttons:
                if button.is_displayed():
                    logging.info(f"Closing modal using selector: {selector}")
                    driver.execute_script("arguments[0].click();", button)
                    time.sleep(2)
    except Exception as e:
        logging.info("No modal appeared or error during dismissal: %s", e)

def scroll_and_click(driver):
    last_height = driver.execute_script("return document.body.scrollHeight")
    retries = 0

    while True:
        driver.execute_script("window.scrollBy(0, 1000);")
        time.sleep(random.uniform(1.2, 1.6))

        try:
            dismiss_modals(driver)
        except:
            pass

        try:
            show_more = driver.find_element(By.XPATH, "//div[contains(@class, 'buttons') and contains(@class, 'show-me-more')]/button")
            if show_more.is_displayed():
                logging.info("Clicking 'Show Me More' button")
                driver.execute_script("arguments[0].click();", show_more)
                time.sleep(random.uniform(2.5, 3.5))
        except:
            pass

        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            retries += 1
            if retries > 3:
                break
        else:
            last_height = new_height
            retries = 0

def extract_data(driver):
    products = []
    elements = driver.find_elements(By.CSS_SELECTOR, "div.grid-item")

    for el in elements:
        try:
            title = el.find_element(By.CSS_SELECTOR, ".product-name a span").text.strip()
            product_url = el.find_element(By.CSS_SELECTOR, ".product-name a").get_attribute("href")
            image_url = el.find_element(By.CSS_SELECTOR, "img.product-image").get_attribute("src")

            price_section = el.find_element(By.CSS_SELECTOR, "[data-test-id='product-pricing']")
            prices = price_section.find_elements(By.CSS_SELECTOR, ".amount")

            sale_price = prices[0].text.strip() if len(prices) > 0 else None
            orig_price = prices[1].text.strip() if len(prices) > 1 else None

            products.append({
                "Product Name": title,
                "Original Price": f"${orig_price}" if orig_price else None,
                "Sale Price": f"${sale_price}" if sale_price else None,
                "Image URL": image_url,
                "Product Display Page URL": product_url,
                "Store": "Pottery Barn"
            })
        except Exception as e:
            logging.warning(f"Skipping product due to error: {e}")
            continue

    return products

def main():
    options = Options()
    options.add_argument("--start-maximized")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    try:
        url = "https://www.potterybarn.com/shop/sale/open-box-deals/"
        driver.get(url)
        time.sleep(5)

        dismiss_modals(driver)
        scroll_and_click(driver)
        data = extract_data(driver)

        with open("pottery_barn_open_box.json", "w") as f:
            json.dump(data, f, indent=2)

        logging.info(f"Scraped {len(data)} products.")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()