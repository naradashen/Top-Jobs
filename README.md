# Top-Jobs
This is a web scraper made by me using selenium. This scrapes every detail in the website using OCR techniques.

## Usage
Run 'ocr.py' to run the scraper headless mode. You can also use other python scripts to run the scraper to extract specific endpoints such as 'junior.py' to extract only junior and entry level jobs.

scrapy runspider spiders/topjobs_spider.py -a num_pages=5 -L INFO
