import requests
from bs4 import BeautifulSoup
import re
import logging
from tqdm import tqdm
import csv

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def scrape_page(url):
    """Fetch and parse the content of a page."""
    try:
        response = requests.get(url)
        response.raise_for_status()  # Check for request errors
        return BeautifulSoup(response.content, 'html.parser')
    except requests.RequestException as e:
        logging.error(f"Request failed: {e}")
        return None

def find_total_pages(base_url):
    """Detect the total number of pages."""
    soup = scrape_page(base_url)
    
    if soup:
        # Find the label with the class 'of-total-pages'
        page_info = soup.find('label', class_='of-total-pages')
        
        if page_info:
            # Extract text and clean it
            page_text = page_info.get_text(strip=True)
            # Remove 'of' and commas, then extract digits
            page_number = re.sub(r'[^\d]', '', page_text)
            return int(page_number) if page_number else 1
    return 1

def scrape_titles_and_links(base_url, total_pages):
    """Scrape titles and links from all pages."""
    all_articles = []

    for page in tqdm(range(1, total_pages + 1), desc="Scraping Pages", unit="page"):
        url = f"{base_url}&page={page}"
        soup = scrape_page(url)
        
        if soup:
            # Find all article entries
            articles = soup.find_all('a', class_='docsum-title')
            
            for article in articles:
                title = article.get_text(strip=True)
                href = article['href']
                all_articles.append((title, f"https://pubmed.ncbi.nlm.nih.gov{href}"))
        else:
            logging.warning(f"Failed to scrape page {page}")
    
    return all_articles

def save_to_csv(articles, filename):
    """Save articles to a CSV file."""
    with open(filename, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(['Title', 'Link'])  # Write header
        for title, link in articles:
            writer.writerow([title, link])  # Write each row

def main():
    search_term = "anxiety disorder"
    base_url = f"https://pubmed.ncbi.nlm.nih.gov/?term={search_term.replace(' ', '+')}"
    
    # Find total number of pages
    total_pages = find_total_pages(base_url)
    logging.info(f"Total pages: {total_pages}")
    
    # Scrape all pages for titles and links
    articles = scrape_titles_and_links(base_url, total_pages)
    
    # Save results to CSV file
    save_to_csv(articles, 'pubmed_articles.csv')
    logging.info("Results have been saved to 'pubmed_articles.csv'.")

if __name__ == "__main__":
    main()
