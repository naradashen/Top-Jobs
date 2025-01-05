import json
import httpx
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pytesseract
from PIL import Image
from io import BytesIO

# Path to the Tesseract executable (update this according to your installation)
pytesseract.pytesseract.tesseract_cmd = r'/usr/bin/tesseract'

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
                
                # Check if position contains keywords 'junior' or 'trainee'
                if any(keyword in position.lower() for keyword in ['intern']):
                    # Initialize the WebDriver
                    driver = webdriver.Chrome()  # Or specify the path to chromedriver.exe if it's not in your PATH

                    # Open the website
                    driver.get(url)

                    # Find the job element and click it
                    job_element = driver.find_element(By.ID, job['id'])
                    job_element.click()

                    # Wait for the new page to load
                    WebDriverWait(driver, 10).until(EC.number_of_windows_to_be(2))

                    # Switch to the new window
                    driver.switch_to.window(driver.window_handles[1])

                    # Now you are on the redirected page, you can scrape the data or perform actions as needed

                    # Extract SEO tags
                    seo_title = driver.title
                    meta_tags = driver.find_elements(By.CSS_SELECTOR, "meta")
                    meta_data = {}
                    for tag in meta_tags:
                        meta_name = tag.get_attribute("name")
                        meta_content = tag.get_attribute("content")
                        if meta_name:
                            meta_data[meta_name] = meta_content
                    
                    # For example, let's extract text from the image
                    try:
                        image_element = driver.find_element(By.CSS_SELECTOR, "#remark img")  # Assuming the image is within the div with id "remark"
                        image_src = image_element.get_attribute("src")
                        image_response = httpx.get(image_src)
                        image = Image.open(BytesIO(image_response.content))
                        extracted_text = pytesseract.image_to_string(image)
                        # Replace newline characters with actual new lines
                        extracted_text = extracted_text.replace('\n', ' ')
                    except Exception as img_exc:
                        print("Error extracting text from image:", img_exc)
                        extracted_text = "N/A"

                    # Close the tab
                    driver.close()

                    # Switch back to the original tab
                    driver.switch_to.window(driver.window_handles[0])

                    # Close the browser
                    driver.quit()
                    
                    job_data = {
                        "Job Reference Number": job_ref,
                        "Position": position,
                        "Employer": employer,
                        "Opening Date": opening_date,
                        "Closing Date": closing_date,
                        "SEO Title": seo_title,
                        "Meta Tags": meta_data,
                        "Extracted Text": extracted_text  # Add extracted text to the dictionary
                    }
                    
                    page_jobs.append(job_data)
                    total_jobs.append(job_data)
                    
                    # Output the scraped data for this job in JSON format
                    print(json.dumps(job_data, indent=4))
                    
            except AttributeError as e:
                print("An error occurred while extracting job details:", e)
        
        print("Total jobs scraped so far:", len(total_jobs))
        
    return total_jobs

def scrape_all_pages():
    base_url = "https://www.topjobs.lk/applicant/vacancybyfunctionalarea.jsp?FA=AV&pageNo="
    num_pages = 5
    total_jobs = []
    
    for page in range(1, num_pages + 1):
        print(f"\n\n\n....................................................................................Scraping page {page}...............................................\n\n\n")  # Print page number just before scraping
        url = f"{base_url}{page}"
        total_jobs = scrape_page(url, page, total_jobs)
    
    print("Total scraped jobs:", len(total_jobs))
    return total_jobs

scraped_data = scrape_all_pages()

# Output the final scraped data in JSON format
with open('scraped_data.json', 'w') as json_file:
    json.dump(scraped_data, json_file, indent=4, ensure_ascii=False)

print("Data saved to scraped_data.json")
