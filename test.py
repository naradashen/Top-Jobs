import json
import httpx
import asyncio
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import sys
import traceback
from datetime import datetime
import pytesseract
from PIL import Image
from io import BytesIO

# Configuration
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}
JSON_FILE = "scraped_data.json"
LOG_FILE = "scraper_errors.log"
PAGES_TO_SCRAPE = 2  # Start with 2 pages for testing
MAX_CONCURRENT_REQUESTS = 3

# Set up logging
def log_error(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    error_msg = f"[{timestamp}] ERROR: {message}"
    print(error_msg, file=sys.stderr)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"{error_msg}\n")

def log_info(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    info_msg = f"[{timestamp}] INFO: {message}"
    print(info_msg)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"{info_msg}\n")

# OCR Setup
try:
    pytesseract.pytesseract.tesseract_cmd = r'/usr/bin/tesseract'
except Exception as e:
    log_error(f"Tesseract initialization failed: {str(e)}")

async def fetch_page(url, client):
    """Fetch page content with retry logic"""
    for attempt in range(3):
        try:
            log_info(f"Fetching {url} (attempt {attempt + 1})")
            response = await client.get(url, headers=HEADERS)
            response.raise_for_status()
            return response.text
        except Exception as e:
            if attempt == 2:
                log_error(f"Failed to fetch {url} after 3 attempts: {str(e)}")
                return None
            await asyncio.sleep(2 * (attempt + 1))

def extract_job_basic(job):
    """Extract basic job info without Selenium"""
    try:
        job_id = job.get('id', 'N/A')
        
        job_ref = (job.find("td", width="5%", align="center").text.strip() 
                  if job.find("td", width="5%", align="center") else "N/A")
        
        position = "N/A"
        job_desc_element = job.find("td", width="28%")
        if job_desc_element:
            for part in job_desc_element.stripped_strings:
                clean_part = part.strip()
                if (clean_part.lower() not in {"company name withheld", "defzzz"} 
                    and not clean_part.startswith("000")):
                    position = clean_part
                    break
        
        employer = (job.find("h1").text.strip() 
                   if job.find("h1") else "N/A")
        
        dates = job.find_all("td", nowrap=True)
        opening_date = dates[1].text.strip() if len(dates) > 1 else "N/A"
        closing_date = dates[2].text.strip() if len(dates) > 2 else "N/A"
        
        return {
            "JobID": job_id,
            "JobReference": job_ref,
            "Position": position,
            "Employer": employer,
            "OpeningDate": opening_date,
            "ClosingDate": closing_date
        }
    except Exception as e:
        log_error(f"Error extracting basic job info: {str(e)}")
        return None

def extract_image_text(image_url):
    """Extract text from image using OCR"""
    try:
        with httpx.Client() as client:
            response = client.get(image_url)
            response.raise_for_status()
            image = Image.open(BytesIO(response.content))
            text = pytesseract.image_to_string(image).replace("\n", " ").strip()
            return text if text else "N/A"
    except Exception as e:
        log_error(f"OCR failed for {image_url}: {str(e)}")
        return "N/A"

async def process_job_detail(driver, job_id, base_data):
    """Process job details using Selenium"""
    try:
        log_info(f"Processing details for job {job_id}")
        
        # Find and click the job element
        job_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, job_id))
        )
        job_element.click()
        
        # Wait for new window and switch
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
        
        # Check for images with OCR
        extracted_text = "N/A"
        try:
            images = driver.find_elements(By.CSS_SELECTOR, "#remark img")
            if images:
                image_src = images[0].get_attribute("src")
                if image_src:
                    extracted_text = extract_image_text(image_src)
        except Exception as e:
            log_error(f"Image processing failed for job {job_id}: {str(e)}")
        
        # Close the detail tab and switch back
        driver.close()
        driver.switch_to.window(driver.window_handles[0])
        
        return {
            **base_data,
            "SEOTitle": seo_title,
            "MetaTags": meta_tags,
            "ExtractedText": extracted_text,
            "ProcessedAt": datetime.now().isoformat()
        }
    except Exception as e:
        log_error(f"Detail processing failed for job {job_id}: {str(e)}")
        return base_data  # Return at least the basic data
    finally:
        # Ensure we don't leave stray windows
        while len(driver.window_handles) > 1:
            driver.switch_to.window(driver.window_handles[1])
            driver.close()
            driver.switch_to.window(driver.window_handles[0])

def init_driver():
    """Initialize Selenium WebDriver"""
    try:
        log_info("Initializing ChromeDriver")
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920,1080")
        
        driver = webdriver.Chrome(options=chrome_options)
        driver.implicitly_wait(5)
        return driver
    except Exception as e:
        log_error(f"Failed to initialize WebDriver: {str(e)}")
        log_error("Please ensure ChromeDriver is installed and in your PATH")
        return None

async def scrape_page(page_num, client, driver):
    """Scrape a single page"""
    log_info(f"Starting page {page_num}")
    
    url = f"https://www.topjobs.lk/applicant/vacancybyfunctionalarea.jsp?FA=AV&pageNo={page_num}"
    html = await fetch_page(url, client)
    if not html:
        return []
    
    try:
        soup = BeautifulSoup(html, "html.parser")
        job_elements = soup.find_all("tr", id=lambda x: x and x.startswith("tr"))
        log_info(f"Found {len(job_elements)} jobs on page {page_num}")
        
        if not job_elements:
            return []
        
        # Process basic info first
        basic_jobs = []
        for job in job_elements:
            basic_info = extract_job_basic(job)
            if basic_info:
                basic_jobs.append(basic_info)
        
        # Process details using Selenium
        detailed_jobs = []
        for job in basic_jobs:
            if not driver:
                driver = init_driver()
                if not driver:
                    return basic_jobs  # Fallback to basic data
                
                # Load the page in Selenium
                driver.get(url)
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.ID, job["JobID"])))
            
            detailed_job = await process_job_detail(driver, job["JobID"], job)
            detailed_jobs.append(detailed_job)
            
            # Save progress after each job
            save_to_json(detailed_job)
        
        return detailed_jobs
    except Exception as e:
        log_error(f"Page {page_num} processing failed: {str(e)}")
        return []

def save_to_json(job_data):
    """Save job data to JSON file"""
    try:
        # Try to load existing data
        try:
            with open(JSON_FILE, "r", encoding="utf-8") as f:
                existing_data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            existing_data = []
        
        # Append new data
        existing_data.append(job_data)
        
        # Save back to file
        with open(JSON_FILE, "w", encoding="utf-8") as f:
            json.dump(existing_data, f, indent=2, ensure_ascii=False)
        
        log_info(f"Saved job: {job_data.get('Position', 'Unknown')}")
    except Exception as e:
        log_error(f"Failed to save JSON: {str(e)}")

async def scrape_all_pages():
    """Main scraping function"""
    start_time = datetime.now()
    log_info("Starting scraping process")
    
    # Initialize HTTP client
    async with httpx.AsyncClient(
        limits=httpx.Limits(max_connections=MAX_CONCURRENT_REQUESTS),
        timeout=httpx.Timeout(30.0),
        headers=HEADERS
    ) as client:
        
        # Initialize Selenium driver
        driver = init_driver()
        if not driver:
            log_error("Cannot proceed without Selenium driver")
            return
        
        try:
            # Process pages sequentially (for stability)
            all_jobs = []
            for page_num in range(1, PAGES_TO_SCRAPE + 1):
                try:
                    page_jobs = await scrape_page(page_num, client, driver)
                    all_jobs.extend(page_jobs)
                except Exception as e:
                    log_error(f"Failed to process page {page_num}: {str(e)}")
                    continue
            
            log_info(f"Scraped {len(all_jobs)} jobs total")
        finally:
            driver.quit()
            log_info("ChromeDriver closed")
    
    duration = datetime.now() - start_time
    log_info(f"Scraping completed in {duration.total_seconds():.2f} seconds")

if __name__ == "__main__":
    try:
        log_info("Script started")
        asyncio.run(scrape_all_pages())
    except KeyboardInterrupt:
        log_info("Scraping interrupted by user")
    except Exception as e:
        log_error(f"Fatal error: {str(e)}")
        traceback.print_exc(file=sys.stderr)
    finally:
        log_info("Script finished")
