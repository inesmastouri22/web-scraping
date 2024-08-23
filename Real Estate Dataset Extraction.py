import pandas as pd
import time
import urllib.parse
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from webdriver_manager.chrome import ChromeDriverManager

# Function to initialize the Selenium driver
def init_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920x1080")
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

# Retry logic to handle WebDriver disconnections
def scrape_page(url, retries=3):
    driver = init_driver()
    for attempt in range(retries):
        try:
            driver.get(url)
            WebDriverWait(driver, 60).until(
                EC.presence_of_element_located((By.CLASS_NAME, 'sc-1dun5hk-0'))
            )
            page_source = driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
            driver.quit()
            return soup
        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            driver.quit()
            if attempt < retries - 1:
                time.sleep(5)
            else:
                raise e

# Function to find the number of pages for a country
def find_total_pages(country):
    initial_url = f'https://www.realestate.com.au/international/{urllib.parse.quote(country)}/p1'
    soup = scrape_page(initial_url)
    
    pagination = soup.find_all('li', class_='ant-pagination-item')
    
    if pagination:
        last_page_number = max([int(page.get('title')) for page in pagination if page.get('title').isdigit()])
        return last_page_number
    else:
        return 1

# Base URL
base_url = 'https://www.realestate.com.au'

# List of country codes to scrape
country_codes = [
    'al', 'ad', 'at', 'be', 'bg', 'hr', 'cy', 'cz', 'ee', 'fi', 'fr', 'de', 'gi', 'gr', 'hu', 'is', 'ie', 
    'it', 'lv', 'lu', 'mt', 'mc', 'nl', 'pl', 'pt', 'ro', 'sk', 'si', 'es', 'se', 'ch', 'tr', 'ua', 'gb',
    'ag', 'ar', 'aw', 'bs', 'bb', 'bz', 'br', 'ca', 'ky', 'cl', 'co', 'cr', 'cu', 'dm', 'do', 'ec', 'sv',
    'gf', 'gd', 'gp', 'gt', 'ht', 'hn', 'jm', 'mx', 'ni', 'pa', 'py', 'pe', 'pr', 'kn', 'lc', 'vc', 'sm',
    'sx', 'tt', 'tc', 'us', 'vi', 'bd', 'kh', 'hk', 'in', 'id', 'jp', 'mo', 'my', 'mv', 'mn', 'mm', 'pk', 
    'ph', 'sg', 'lk', 'tw', 'th', 'vn', 'il', 'jo', 'om', 'sa', 'ae', 'dz', 'bi', 'cv', 'eg', 'gh', 'ke', 
    'mg', 'mu', 'ma', 'ng', 're', 'za', 'tn', 'zm', 'fj', 'nz', 'vu'
]

# List to store property data
property_data = []
record_counter = 0

# Loop through each country and dynamically determine the number of pages
for country in country_codes:
    try:
        total_pages = find_total_pages(country)
        print(f"{country} has {total_pages} pages")

        for i in range(1, total_pages + 1):
            page_url = f'{base_url}/international/{urllib.parse.quote(country)}/p{i}'
            print(f'Scraping URL: {page_url}')

            try:
                soup = scrape_page(page_url)
                
                # Extract property details
                property_listings = soup.find_all('div', class_='sc-1dun5hk-0')

                for listing in property_listings:
                    # Extract the link and prepend the base URL
                    link_element = listing.find('a')
                    href = base_url + link_element.get('href', '') if link_element else 'No link found'
                    print(f"Extracted Link: {href}")

                    # Extract the property type
                    property_type_element = listing.find('div', class_='property-type')
                    property_type = property_type_element.text.strip() if property_type_element else 'N/A'
                    print(f"Extracted Property Type: {property_type}")

                    # Extract the address
                    address_element = listing.find('div', class_='address')
                    address = address_element.text.strip() if address_element else 'N/A'
                    print(f"Extracted Address: {address}")

                    # Extract the price
                    price_element = listing.find('div', class_='displayListingPrice')
                    price = price_element.text.strip() if price_element else 'N/A'
                    print(f"Extracted Price: {price}")

                    # Extract all feature-items
                    features = listing.find_all('div', class_='feature-item')

                    # Initialize variables to hold the details
                    bedrooms = 'N/A'
                    bathrooms = 'N/A'
                    building_size = 'N/A'

                    # Extract details based on feature-item content
                    for feature in features:
                        img_alt = feature.find('img')['alt']
                        if 'bedrooms' in img_alt:
                            bedrooms = feature.get_text(strip=True)
                        elif 'bathroom' in img_alt:
                            bathrooms = feature.get_text(strip=True)
                        elif 'buildingSize' in img_alt:
                            building_size = feature.get_text(strip=True)

                    print(f"Extracted Bedrooms: {bedrooms}")
                    print(f"Extracted Bathrooms: {bathrooms}")
                    print(f"Extracted Building Size: {building_size}")

                    # Append the extracted data to the list
                    property_data.append((country, address, property_type, price, bedrooms, bathrooms, building_size, href))
                    record_counter += 1

                    # Save data to CSV every 20 records
                    if record_counter % 20 == 0:
                        df = pd.DataFrame(property_data, columns=['Country', 'Address', 'Property Type', 'Price', 'Bedrooms', 'Bathrooms', 'Building Size', 'Link'])
                        df.to_csv('property_listings.csv', mode='a', header=False, index=False)
                        print(f"Saved {record_counter} records to CSV.")

                    # Adding a small delay to avoid being blocked
                    time.sleep(5)

            except Exception as e:
                print(f"Error scraping {page_url}: {e}")
    
    except Exception as e:
        print(f"Error processing country {country}: {e}")

# Save any remaining data to CSV
if property_data:
    df = pd.DataFrame(property_data, columns=['Country', 'Address', 'Property Type', 'Price', 'Bedrooms', 'Bathrooms', 'Building Size', 'Link'])
    df.to_csv('property_listings.csv', mode='a', header=False, index=False)
    print("Final data saved to CSV.")
