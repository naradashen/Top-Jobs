import json
import httpx
import asyncio
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
from concurrent.futures import ThreadPoolExecutor

# Configuration
pytesseract.pytesseract.tesseract_cmd = r'/usr/bin/tesseract'
HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
}
JSON_FILE = "scraped_data.json"
MAX_WORKERS = 5  # Number of concurrent threads for Selenium operations

# Initialize Chrome options for headless browsing
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("window-size=1920,1080")

def save_to_json(job_data):
    """Appends job data to the JSON file in real time with the exact required format"""
    try:
        with open(JSON_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        data = []

    data.append({
        "Job Reference Number": job_data.get("Job Reference Number", "N/A"),
        "Position": job_data.get("Position", "N/A"),
        "Employer": job_data.get("Employer", "N/A"),
        "Opening Date": job_data.get("Opening Date", "N/A"),
        "Closing Date": job_data.get("Closing Date", "N/A"),
        "SEO Title": job_data.get("SEO Title", "N/A"),
        "Meta Tags": job_data.get("Meta Tags", {}),
        "Extracted Text": job_data.get("Extracted Text", "N/A")
    })

    with open(JSON_FILE, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4, ensure_ascii=False)

    print(f"Job saved: {job_data.get('Position', 'Unknown')}")

def extract_image_text(image_url):
    """Extracts text from an image using OCR with error handling"""
    try:
        with httpx.Client() as client:
            response = client.get(image_url, headers=HEADERS)
            response.raise_for_status()
            image = Image.open(BytesIO(response.content))
            text = pytesseract.image_to_string(image).replace("\n", " ").strip()
            return text if text else "N/A"
    except Exception as e:
        print(f"Error extracting text from image: {e}")
        return "N/A"

def process_job_detail(driver, job_element, base_data):
    """Processes job details using Selenium with the exact original format"""
    try:
        # Click the job element
        job_element.click()
        
        # Wait for new tab and switch
        WebDriverWait(driver, 10).until(lambda d: len(d.window_handles) > 1)
        driver.switch_to.window(driver.window_handles[1])
        
        # Get page details
        seo_title = driver.title
        
        # Extract meta tags
        meta_tags = {}
        for tag in driver.find_elements(By.CSS_SELECTOR, "meta[name]"):
            name = tag.get_attribute("name")
            if name:
                meta_tags[name] = tag.get_attribute("content")
        
        # Extract image text if present
        extracted_text = "N/A"
        try:
            image_element = driver.find_element(By.CSS_SELECTOR, "#remark img")
            image_src = image_element.get_attribute("src")
            if image_src:
                extracted_text = extract_image_text(image_src)
        except Exception:
            pass
        
        # Prepare the complete job data
        job_data = {
            **base_data,
            "SEO Title": seo_title,
            "Meta Tags": meta_tags,
            "Extracted Text": extracted_text
        }
        
        return job_data
    except Exception as e:
        print(f"Error processing job details: {e}")
        return base_data  # Return at least the basic data
    finally:
        # Close the detail tab and switch back
        if len(driver.window_handles) > 1:
            driver.close()
            driver.switch_to.window(driver.window_handles[0])

def scrape_page_with_selenium(url, page_number):
    """Scrapes a single page using Selenium with the exact original output format"""
    try:
        # Initialize Selenium WebDriver
        driver = webdriver.Chrome(options=chrome_options)
        driver.get(url)
        time.sleep(2)  # Initial page load
        
        # Wait for jobs to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "tr[id^='tr']")))
        
        # Get all job elements
        job_elements = driver.find_elements(By.CSS_SELECTOR, "tr[id^='tr']")
        
        for job_element in job_elements:
            try:
                # Extract basic info from the job row
                job_ref = job_element.find_element(By.CSS_SELECTOR, "td[width='5%'][align='center']").text.strip()
                
                # Extract position (special handling for DEFZZZ cases)
                position = "N/A"
                job_desc_element = job_element.find_element(By.CSS_SELECTOR, "td[width='28%']")
                job_desc_parts = [part.strip() for part in job_desc_element.text.split("\n") if part.strip()]
                
                for part in job_desc_parts:
                    if part != "DEFZZZ" and not part.startswith("000") and part.lower() != "company name withheld":
                        position = part
                        break
                
                # Extract employer
                employer = job_element.find_element(By.TAG_NAME, "h1").text.strip()
                
                # Extract dates
                date_elements = job_element.find_elements(By.CSS_SELECTOR, "td[nowrap]")
                opening_date = date_elements[1].text.strip() if len(date_elements) > 1 else "N/A"
                closing_date = date_elements[2].text.strip() if len(date_elements) > 2 else "N/A"
                
                # Prepare base data
                base_data = {
                    "Job Reference Number": job_ref,
                    "Position": position,
                    "Employer": employer,
                    "Opening Date": opening_date,
                    "Closing Date": closing_date
                }
                
                # Process job details
                job_data = process_job_detail(driver, job_element, base_data)
                
                # Save the job data
                save_to_json(job_data)
                
            except Exception as e:
                print(f"Error processing job: {e}")
                continue
        
    except Exception as e:
        print(f"Error scraping page {page_number}: {e}")
    finally:
        if driver:
            driver.quit()

async def scrape_all_pages_fast():
    """Main scraping function that maintains the original format but runs faster"""
    base_url = "https://www.topjobs.lk/applicant/vacancybyfunctionalarea.jsp?FA=AV&pageNo="
    num_pages = 5  # Adjust as needed
    
    # Use ThreadPoolExecutor to parallelize Selenium operations
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        # Create tasks for each page
        futures = []
        for page in range(1, num_pages + 1):
            url = f"{base_url}{page}"
            futures.append(executor.submit(scrape_page_with_selenium, url, page))
        
        # Wait for all tasks to complete
        for future in futures:
            try:
                future.result()  # This will re-raise any exceptions that occurred
            except Exception as e:
                print(f"Error in page processing: {e}")
    
    print("\nScraping completed. Data saved to 'scraped_data.json'.")

# Start the scraping process
if __name__ == "__main__":
    start_time = time.time()
    asyncio.run(scrape_all_pages_fast())
    print(f"Total execution time: {time.time() - start_time:.2f} seconds")
