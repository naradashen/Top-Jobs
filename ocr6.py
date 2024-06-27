from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
import time

def extract_details_with_ocr(total_jobs, driver):
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
                
                # Find the element to left-click and redirect
                element = driver.find_element(By.XPATH, "//tr[@id='tr0']")  # Update XPath as needed
                ActionChains(driver).click(element).perform()

                # Wait for the page redirection
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

# Assume other functions and imports are present

# Main function
def scrape_all_pages_and_extract_details():
    base_url = "https://www.topjobs.lk/applicant/vacancybyfunctionalarea.jsp?FA=AV&pageNo="
    num_pages = 6
    total_jobs = []
    
    options = Options()
    options.add_argument('--headless')  # Run headless browser
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    service = Service('/usr/local/bin/chromedriver')  # Update path to your chromedriver

    driver = webdriver.Chrome(service=service, options=options)

    try:
        for page in range(1, num_pages + 1):
            print(f"\n\n\n....................................................................................Scraping page {page}...............................................\n\n\n")  # Print page number just before scraping
            url = f"{base_url}{page}"
            scrape_page(url, page, total_jobs)
        
        print("Total scraped jobs:", len(total_jobs))

        # Extract details with OCR using Selenium
        extract_details_with_ocr(total_jobs, driver)

    finally:
        # Close the browser
        print("Closing the browser...")
        driver.quit()

scrape_all_pages_and_extract_details()
