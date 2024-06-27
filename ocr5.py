import httpx
from bs4 import BeautifulSoup
import pytesseract
from PIL import Image
from io import BytesIO
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import time

# Function to perform OCR on an image
def ocr_image(image):
    try:
        text = pytesseract.image_to_string(image)
        return text.strip()
    except Exception as e:
        print("Error occurred during OCR:", e)
        return ""

# Function to scrape job details from the main page using httpx and BeautifulSoup
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
                if job_ref_element:
                    job_ref = job_ref_element.text.strip()
                else:
                    job_ref = "N/A"
                
                position_element = job.find('span', id='hdnJC1')
                if position_element:
                    position = position_element.text.strip()
                else:
                    position = "N/A"
                
                if position == "N/A":  # If position is not found in designated element, try to extract from job description
                    job_desc_element = job.find('td', width="28%")
                    if job_desc_element:
                        job_desc_parts = [part.strip() for part in job_desc_element.stripped_strings if part != "DEFZZZ" and not part.startswith("000")]
                        for part in job_desc_parts:
                            if part.lower() != "company name withheld":
                                position = part
                                break
                
                employer_element = job.find('h1')
                if employer_element:
                    employer = employer_element.text.strip()
                else:
                    employer = "N/A"
                
                opening_date_elements = job.find_all('td', nowrap=True)
                if opening_date_elements and len(opening_date_elements) >= 2:
                    opening_date = opening_date_elements[1].text.strip()
                    closing_date = opening_date_elements[2].text.strip()
                else:
                    opening_date = "N/A"
                    closing_date = "N/A"
                
                # Extract data for navigation
                onclick_attr = job.get('onclick')
                rid = onclick_attr.split("'")[1]
                ac = onclick_attr.split("'")[3]
                jc = onclick_attr.split("'")[5]
                ec = onclick_attr.split("'")[7]
                pg = 'applicant/vacancybyfunctionalarea.jsp'
                job_data = {
                    "Job Reference Number": job_ref,
                    "Position": position,
                    "Employer": employer,
                    "Opening Date": opening_date,
                    "Closing Date": closing_date,
                    "rid": rid,
                    "ac": ac,
                    "jc": jc,
                    "ec": ec,
                    "pg": pg
                }

                # Output in piped format
                print("|".join([f"Job Reference Number: {job_ref}", f"Position: {position}", f"Employer: {employer}", f"Opening Date: {opening_date}", f"Closing Date: {closing_date}"]))
                print("\n")
                
                page_jobs.append(job_data)
                
            except AttributeError as e:
                print("An error occurred while extracting job details:", e)
        
        total_jobs.extend(page_jobs)

# Function to use Selenium to click job listings and extract details using OCR
def extract_details_with_ocr(total_jobs):
    # Setup Selenium WebDriver (Assuming Chrome)
    options = Options()
    options.add_argument('--headless')  # Run headless browser
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    service = Service('/usr/local/bin/chromedriver')  # Update path to your chromedriver

    driver = webdriver.Chrome(service=service, options=options)

    try:
        for index, job_data in enumerate(total_jobs):
            try:
                print(f"Processing job listing {index + 1}...")

                # Construct the URL based on the provided attributes
                rid = job_data['rid']
                ac = job_data['ac']
                jc = job_data['jc']
                ec = job_data['ec']
                pg = job_data['pg']
                job_url = f"https://www.topjobs.lk/employer/JobAdvertismentServlet?rid={rid}&ac={ac}&jc={jc}&ec={ec}&pg={pg}"
                
                # Navigate to the job details page
                driver.get(job_url)
                
                # Wait for the new page to load
                time.sleep(2)
                
                # Take a screenshot of the page for OCR
                screenshot = driver.get_screenshot_as_png()
                image = Image.open(BytesIO(screenshot))

                # Perform OCR on the screenshot
                extracted_text = ocr_image(image)
                print(f"Extracted Text from Page {index + 1}:")
                print(extracted_text)

                # Navigate back to the previous page to continue with the next job listing
                driver.back()
                time.sleep(2)  # Wait for the page to load

            except Exception as e:
                print(f"Error processing job listing {index + 1}: {e}")

    finally:
        # Close the browser
        print("Closing the browser...")
        driver.quit()

# Main function to scrape all pages and extract details with OCR
def scrape_all_pages_and_extract_details():
    base_url = "https://www.topjobs.lk/applicant/vacancybyfunctionalarea.jsp?FA=AV&pageNo="
    num_pages = 6
    total_jobs = []
    
    for page in range(1, num_pages + 1):
        print(f"\n\n\n....................................................................................Scraping page {page}...............................................\n\n\n")  # Print page number just before scraping
        url = f"{base_url}{page}"
        scrape_page(url, page, total_jobs)
    
    print("Total scraped jobs:", len(total_jobs))

    # Extract details with OCR using Selenium
    extract_details_with_ocr(total_jobs)

scrape_all_pages_and_extract_details()
