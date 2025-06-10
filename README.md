# 🔍 TopJobs.lk Job Scraper

This project is a robust, OCR-enabled job scraper built in Python for extracting detailed job postings from [TopJobs.lk](https://www.topjobs.lk). It uses **Selenium**, **BeautifulSoup**, and **Tesseract OCR** to fetch and process both text and image-based job data, storing it in a structured JSON format.

---

## 📌 Features

- ✅ Headless Chrome automation via Selenium
- ✅ Intelligent job metadata parsing
- ✅ OCR support for embedded images (job ads)
- ✅ Timestamped logging for process tracking
- ✅ Fault-tolerant and resilient scraping
- ✅ Real-time JSON appending and persistence

---

## ⚙️ Requirements

- Python 3.7+
- Google Chrome + chromedriver (compatible version)
- Tesseract OCR installed

```bash
pip3 install selenium httpx beautifulsoup4 pytesseract Pillow


---

## 🛠️ Installation

1. **Clone the repository**
```bash
git clone https://github.com/naradashen/Top-Jobs.git
cd Top-Jobs

---

## 🚀 Usage

```bash
python3 ocr.py (slow)
python3 main.py (fast)
