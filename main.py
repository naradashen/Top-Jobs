import json
import httpx
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pytesseract
from PIL import Image
from io import BytesIO
import time
import sys

# Configuration
pytesseract.pytesseract.tesseract_cmd = r'/usr/bin/tesseract'
HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
}
JSON_FILE = "scraped_data.json"

# Set up Chrome options
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("window-size=1920,1080")

def print_progress(message):
    """Print progress messages with timestamp"""
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}", flush=True)

def save_to_json(job_data):
    """Save job data to JSON file"""
    try:
        # Load existing data or create new list
        try:
            with open(JSON_FILE, "r", encoding="utf-8") as file:
                data = json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            data = []
        
        # Append new job data
        data.append(job_data)
        
        # Save back to file
        with open(JSON_FILE, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=4, ensure_ascii=False)
            
    except Exception as e:
        print_progress(f"Error saving to JSON: {e}")

def extract_image_text(image_url):
    """Extract text from image using OCR"""
    try:
        print_progress(f"Processing image: {image_url}")
        with httpx.Client() as client:
            response = client.get(image_url, headers=HEADERS, timeout=10)
            response.raise_for_status()
            image = Image.open(BytesIO(response.content))
            text = pytesseract.image_to_string(image).replace("\n", " ").strip()
            return text if text else "N/A"
    except Exception as e:
        print_progress(f"OCR Error: {e}")
        return "N/A"

def scrape_job_page(driver, job_element):
    """Scrape individual job details"""
    try:
        # Extract basic info
        job_ref = job_element.find_element(By.CSS_SELECTOR, "td[width='5%'][align='center']").text.strip()
        
        # Position extraction with special cases
        position = "N/A"
        job_desc_element = job_element.find_element(By.CSS_SELECTOR, "td[width='28%']")
        job_desc_parts = [part.strip() for part in job_desc_element.text.split("\n") if part.strip()]
        
        for part in job_desc_parts:
            if part != "DEFZZZ" and not part.startswith("000") and part.lower() != "company name withheld":
                position = part
                break
        
        employer = job_element.find_element(By.TAG_NAME, "h1").text.strip()
        
        # Date extraction
        date_elements = job_element.find_elements(By.CSS_SELECTOR, "td[nowrap]")
        opening_date = date_elements[1].text.strip() if len(date_elements) > 1 else "N/A"
        closing_date = date_elements[2].text.strip() if len(date_elements) > 2 else "N/A"
        
        # Click to open details
        job_element.click()
        
        # Switch to new tab
        WebDriverWait(driver, 10).until(lambda d: len(d.window_handles) > 1)
        driver.switch_to.window(driver.window_handles[1])
        
        # Get details from new tab
        seo_title = driver.title
        
        # Extract meta tags
        meta_tags = {}
        for tag in driver.find_elements(By.CSS_SELECTOR, "meta[name]"):
            name = tag.get_attribute("name")
            if name:
                meta_tags[name] = tag.get_attribute("content")
        
        # Image text extraction
        extracted_text = "N/A"
        try:
            img_elements = driver.find_elements(By.CSS_SELECTOR, "#remark img")
            if img_elements:
                image_src = img_elements[0].get_attribute("src")
                if image_src:
                    extracted_text = extract_image_text(image_src)
        except Exception as e:
            print_progress(f"Image processing error: {e}")
        
        # Prepare final data
        job_data = {
            "Job Reference Number": job_ref,
            "Position": position,
            "Employer": employer,
            "Opening Date": opening_date,
            "Closing Date": closing_date,
            "SEO Title": seo_title,
            "Meta Tags": meta_tags,
            "Extracted Text": extracted_text
        }
        
        return job_data
        
    except Exception as e:
        print_progress(f"Job processing error: {e}")
        return None
    finally:
        # Clean up tabs
        while len(driver.window_handles) > 1:
            driver.switch_to.window(driver.window_handles[1])
            driver.close()
        if len(driver.window_handles) > 0:
            driver.switch_to.window(driver.window_handles[0])

def scrape_page(url, page_num):
    """Scrape a single page of jobs"""
    print_progress(f"Starting page {page_num}")
    
    try:
        # Initialize browser
        driver = webdriver.Chrome(options=chrome_options)
        driver.get(url)
        
        # Wait for jobs to load
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "tr[id^='tr']")))
        
        # Get all job elements
        job_elements = driver.find_elements(By.CSS_SELECTOR, "tr[id^='tr']")
        print_progress(f"Found {len(job_elements)} jobs on page {page_num}")
        
        # Process each job
        for i, job_element in enumerate(job_elements, 1):
            print_progress(f"Processing job {i}/{len(job_elements)} on page {page_num}")
            job_data = scrape_job_page(driver, job_element)
            if job_data:
                save_to_json(job_data)
                print_progress(f"Saved: {job_data['Position'][:50]}...")
        
        print_progress(f"Finished page {page_num}")
        
    except Exception as e:
        print_progress(f"Page {page_num} error: {e}")
    finally:
        if 'driver' in locals():
            driver.quit()

def main():
    """Main scraping function"""
    print_progress("Starting scraping process")
    start_time = time.time()
    
    base_url = "https://www.topjobs.lk/applicant/vacancybyfunctionalarea.jsp?FA=AV&pageNo="
    pages_to_scrape = 2  # Start with 2 pages for testing
    
    try:
        for page_num in range(1, pages_to_scrape + 1):
            scrape_page(f"{base_url}{page_num}", page_num)
        
        print_progress("Scraping completed successfully")
    except KeyboardInterrupt:
        print_progress("Scraping interrupted by user")
    except Exception as e:
        print_progress(f"Fatal error: {e}")
    finally:
        duration = time.time() - start_time
        print_progress(f"Total execution time: {duration:.2f} seconds")

if __name__ == "__main__":
    main()
