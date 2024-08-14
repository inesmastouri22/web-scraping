from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import pandas as pd
import time
import urllib.parse
# Download the ChromeDriver First
# Path to the ChromeDriver executable
chromedriver_path = 'C:/Users/DELL/Downloads/chromedriver-win64/chromedriver-win64/chromedriver.exe'  # Update this to the actual path

# Function to initialize the Selenium driver
def init_driver():
    chrome_options = Options()
    # Uncomment the next line to enable headless mode, otherwise run in normal mode for testing
    # chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920x1080")
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    return webdriver.Chrome(service=Service(chromedriver_path), options=chrome_options)

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
            driver.quit()  # Close the driver after successful operation
            return soup
        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            driver.quit()  # Ensure driver is closed on failure
            if attempt < retries - 1:
                time.sleep(5)  # Wait before retrying
            else:
                raise e  # Raise the exception if all retries fail

# Function to find the number of pages for a country
def find_total_pages(country):
    initial_url = f'https://www.realestate.com.au/international/{urllib.parse.quote(country)}/p1'
    soup = scrape_page(initial_url)
    
    # Look for the last page number in the pagination
    pagination = soup.find_all('li', class_='ant-pagination-item')
    
    if pagination:
        last_page_number = max([int(page.get('title')) for page in pagination if page.get('title').isdigit()])
        return last_page_number
    else:
        return 1  # Default to 1 if no pagination is found

# List of country codes to scrape based on your provided images
country_codes = [
    'al', 'ad', 'at', 'be', 'bg', 'hr', 'cy', 'cz', 'ee', 'fi', 'fr', 'de', 'gi', 'gr', 'hu', 'is', 'ie', 
    'it', 'lv', 'lu', 'mt', 'mc', 'nl', 'pl', 'pt', 'ro', 'sk', 'si', 'es', 'se', 'ch', 'tr', 'ua', 'gb',
    'ag', 'ar', 'aw', 'bs', 'bb', 'bz', 'br', 'ca', 'ky', 'cl', 'co', 'cr', 'cu', 'dm', 'do', 'ec', 'sv',
    'gf', 'gd', 'gp', 'gt', 'ht', 'hn', 'jm', 'mx', 'ni', 'pa', 'py', 'pe', 'pr', 'kn', 'lc', 'vc', 'sm',
    'sx', 'tt', 'tc', 'us', 'vi', 'bd', 'kh', 'hk', 'in', 'id', 'jp', 'mo', 'my', 'mv', 'mn', 'mm', 'pk', 
    'ph', 'sg', 'lk', 'tw', 'th', 'vn', 'il', 'jo', 'om', 'sa', 'ae', 'dz', 'bi', 'cv', 'eg', 'gh', 'ke', 
    'mg', 'mu', 'ma', 'ng', 're', 'za', 'tn', 'zm', 'fj', 'nz', 'vu'
]

# Base URL
base_url = 'https://www.realestate.com.au'

# List to store property data
property_data = []

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
                    if property_type_element:
                        property_type = property_type_element.text.strip()
                        print(f"Extracted Property Type: {property_type}")
                    else:
                        property_type = 'N/A'
                        print("Property type element not found.")

                    # Extract the address
                    address_element = listing.find('div', class_='address')
                    if address_element:
                        address = address_element.text.strip()
                        print(f"Extracted Address: {address}")
                    else:
                        address = 'N/A'
                        print("Address element not found.")

                    # Extract the price
                    price_element = listing.find('div', class_='displayListingPrice')
                    if price_element:
                        price = price_element.text.strip()
                        print(f"Extracted Price: {price}")
                    else:
                        price = 'N/A'
                        print("Price element not found.")

                    # Extract all feature-items
                    features = listing.find_all('div', class_='feature-item')

                    # Initialize variables to hold the details
                    bedrooms = 'N/A'
                    bathrooms = 'N/A'
                    building_size = 'N/A'

                    # Extract details based on feature-item content
                    for feature in features:
                        # Check for bedrooms, bathrooms, and building size
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

                    # Adding a small delay to avoid being blocked
                    time.sleep(5)

            except Exception as e:
                print(f"Error scraping {page_url}: {e}")
    
    except Exception as e:
        print(f"Error processing country {country}: {e}")

# Create a DataFrame and display it
df = pd.DataFrame(property_data, columns=['Country', 'Address', 'Property Type', 'Price', 'Bedrooms', 'Bathrooms', 'Building Size', 'Link'])
print(df)

# Save the DataFrame to a CSV file
df.to_csv('C:/Users/DELL/Desktop/property_listings_by_country new.csv', index=False)
