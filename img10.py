import json
import httpx
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import pytesseract
from PIL import Image
from io import BytesIO
import os

# Path to the Tesseract executable (update this according to your installation)
pytesseract.pytesseract.tesseract_cmd = r'/usr/bin/tesseract'

# Initialize the WebDriver in headless mode
def init_driver():
    options = Options()
    options.add_argument('--headless')  # Ensure headless mode is enabled
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')  # Fix for limited shared memory in some environments
    options.add_argument('--window-size=1920,1080')  # Set a fixed window size for headless mode
    options.add_argument('--remote-debugging-port=9222')  # Useful for debugging if needed

    chromedriver_path = "/usr/local/bin/chromedriver"  # Update this path
    service = Service(chromedriver_path)
    driver = webdriver.Chrome(service=service, options=options)
    return driver

def scrape_page(url, page_number, total_jobs):
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
    }
    
    with httpx.Client() as client:
        response = client.get(url, headers=headers)
    
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        job_listings = soup.find_all('tr', id=lambda x: x and x.startswith('tr'))
        
        page_jobs = []
        
        for job in job_listings:
            try:
                job_ref_element = job.find('td', width="5%", align="center")
                job_ref = job_ref_element.text.strip() if job_ref_element else "N/A"
                
                position_element = job.find('span', id='hdnJC1')
                position = position_element.text.strip() if position_element else "N/A"
                
                if position == "N/A":
                    job_desc_element = job.find('td', width="28%")
                    if job_desc_element:
                        job_desc_parts = [
                            part.strip() for part in job_desc_element.stripped_strings 
                            if part != "DEFZZZ" and not part.startswith("000")
                        ]
                        for part in job_desc_parts:
                            if part.lower() != "company name withheld":
                                position = part
                                break
                
                employer_element = job.find('h1')
                employer = employer_element.text.strip() if employer_element else "N/A"
                
                opening_date_elements = job.find_all('td', nowrap=True)
                if opening_date_elements and len(opening_date_elements) >= 2:
                    opening_date = opening_date_elements[1].text.strip()
                    closing_date = opening_date_elements[2].text.strip()
                else:
                    opening_date, closing_date = "N/A", "N/A"
                
                driver = init_driver()
                driver.get(url)
                
                job_element = driver.find_element(By.ID, job['id'])
                job_element.click()
                
                WebDriverWait(driver, 10).until(EC.number_of_windows_to_be(2))
                driver.switch_to.window(driver.window_handles[1])
                
                seo_title = driver.title
                meta_tags = driver.find_elements(By.CSS_SELECTOR, "meta")
                meta_data = {
                    tag.get_attribute("name"): tag.get_attribute("content") 
                    for tag in meta_tags if tag.get_attribute("name")
                }
                
                try:
                    image_element = driver.find_element(By.CSS_SELECTOR, "#remark img")
                    image_src = image_element.get_attribute("src")
                    image_response = httpx.get(image_src)
                    image = Image.open(BytesIO(image_response.content))
                    extracted_text = pytesseract.image_to_string(image).replace('\n', ' ')
                except Exception as img_exc:
                    print("Error extracting text from image:", img_exc)
                    extracted_text = "N/A"
                
                driver.close()
                driver.switch_to.window(driver.window_handles[0])
                driver.quit()
                
                job_data = {
                    "Job Reference Number": job_ref,
                    "Position": position,
                    "Employer": employer,
                    "Opening Date": opening_date,
                    "Closing Date": closing_date,
                    "SEO Title": seo_title,
                    "Meta Tags": meta_data,
                    "Extracted Text": extracted_text
                }
                
                page_jobs.append(job_data)
                total_jobs.append(job_data)
                print(json.dumps(job_data, indent=4))
                
            except Exception as e:
                print("An error occurred while extracting job details:", e)
        
        print("Total jobs scraped so far:", len(total_jobs))

def scrape_all_pages():
    base_url = "https://www.topjobs.lk/applicant/vacancybyfunctionalarea.jsp?FA=AV&pageNo="
    num_pages = 5
    total_jobs = []
    
    for page in range(1, num_pages + 1):
        print(f"\nScraping page {page}...\n")
        url = f"{base_url}{page}"
        scrape_page(url, page, total_jobs)
    
    print("Total scraped jobs:", len(total_jobs))
    return total_jobs

scraped_data = scrape_all_pages()

with open('scraped_data.json', 'w') as json_file:
    json.dump(scraped_data, json_file, indent=4, ensure_ascii=False)

print("Data saved to scraped_data.json")
