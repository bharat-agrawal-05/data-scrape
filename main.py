# %%
import os
import time
import hashlib
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from PyPDF2 import PdfReader
from langdetect import detect
from datetime import datetime
import json
import pytesseract
from pdf2image import convert_from_path

# %%
DOWNLOAD_DIR = "downloads"
JSON_OUTPUT_DIR = "json_output"
HEADERS = {'User-Agent': 'bot/1.0'}
DELAY = 1
SUPPORTED_FORMATS = ['.pdf', '.epub', '.html']
CHECKSUMS_FILE = 'checksums.json'

# %%
def ensure_dirs():
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    os.makedirs(JSON_OUTPUT_DIR, exist_ok=True)

def sha256_checksum(file_path):
    with open(file_path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def crawl_and_download(base_url, visited=set()):
    if base_url in visited:
        return
    visited.add(base_url)


    try:
        res = requests.get(base_url, headers=HEADERS)
        time.sleep(DELAY)
        if res.status_code != 200:
            print(f"Failed to access {base_url}: {res.status_code}")
            return 
        soup = BeautifulSoup(res.content, 'html.parser')
        for link in soup.find_all("a"):
            href = link.get("href")
            if not href:
                continue
            full_url = urljoin(base_url, href)
            parsed = urlparse(full_url)
            ext = os.path.splitext(parsed.path)[1].lower()

            if ext in SUPPORTED_FORMATS:
                download_file(full_url)
            elif parsed.netloc == urlparse(base_url).netloc:
                crawl_and_download(full_url, visited)
    except Exception as e:
        print(f"Error crawling {base_url}: {e}")

def download_file(url):
    try:
        file_name = os.path.basename(urlparse(url).path)
        domain = urlparse(url).netloc.replace('.', '_')
        domain_folder = os.path.join(DOWNLOAD_DIR, domain)
        os.makedirs(domain_folder, exist_ok=True)
        file_path = os.path.join(domain_folder, file_name)

        if os.path.exists(file_path):
            while(os.path.exists(file_path)):
                file_name = f"{os.path.splitext(file_name)[0]}_{int(time.time())}{os.path.splitext(file_name)[1]}"
                file_path = os.path.join(domain_folder, file_name)

        print(f"Downloading {url} to {file_path}")

        r = requests.get(url, headers=HEADERS)
        if r.status_code == 200:
            with open(file_path, 'wb') as f:
                f.write(r.content)
            return file_path
        
    except Exception as e:
        print(f"Failed to download {url}: {e}")
    return None

def extract_text_and_metadata(file_path):
    content = ""
    title, author, pub_year, language = None, None, None, "Unknown"
    try:
        reader = PdfReader(file_path)
        info = reader.metadata
        content = "\n".join([page.extract_text() or "" for page in reader.pages])
        title = info.title if info else None
        author = info.author if info else None
        language = detect(content[:200]) if content else "Unknown"
    except Exception:
        try:
            print(f"Attempting OCR on {file_path}...")
            images = convert_from_path(file_path)
            content = "\n".join([pytesseract.image_to_string(img) for img in images])
            language = detect(content[:200]) if content else "Unknown"
        except Exception as e:
            print(f"OCR failed for {file_path}: {e}")

    try:
        pub_year = extract_pub_year(content)
    except:
        pub_year = None
    return content.strip(), title, author, pub_year, language

def extract_pub_year(text):
    import re
    match = re.search(r'\b(19|20)\d{2}\b', text)
    return match.group(0) if match else None

def load_checksums():
    if os.path.exists(CHECKSUMS_FILE):
        with open(CHECKSUMS_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_checksums(checksums):
    with open(CHECKSUMS_FILE, 'w') as f:
        json.dump(checksums, f, indent=2)

def build_json_record(file_path, url):
    domain = urlparse(url).netloc
    checksum = sha256_checksum(file_path)
    checksums = load_checksums()
    document_id = os.path.splitext(os.path.basename(file_path))[0] + "_" + checksum[:8]
    # delta processing check with checksum
    if checksums.get(document_id) == checksum:
        print(f"Skipping unchanged document: {document_id}")
        return
    
    scraped_at = datetime.utcnow().isoformat() + "Z"
    document_id = os.path.splitext(os.path.basename(file_path))[0] + "_" + checksum[:8]
    content, title, author, pub_year, language = extract_text_and_metadata(file_path)

    record = {
        "site": domain,
        "document_id": document_id,
        "title": title or "Untitled Document",
        "authors": [author] if author else [],
        "pub_year": pub_year,
        "language": language,
        "download_url": url,
        "checksum": checksum,
        "scraped_at": scraped_at,
        "content": content
    }

    json_path = os.path.join(JSON_OUTPUT_DIR, f"{document_id}.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(record, f, ensure_ascii=False, indent=2)

    print(f"Saved metadata: {json_path}")
    checksums[document_id] = checksum
    save_checksums(checksums)

def run_pipeline(target_urls):
    ensure_dirs()
    for url in target_urls:
        crawl_and_download(url)
        domain_folder = os.path.join(DOWNLOAD_DIR, urlparse(url).netloc.replace('.', '_'))
        if os.path.exists(domain_folder):
            for root, _, files in os.walk(domain_folder):
                for file in files:
                    file_path = os.path.join(root, file)
                    build_json_record(file_path, urljoin(url, file))


# %%
TARGET_URLS = open("links.txt").read().splitlines()

if not TARGET_URLS:
    print("No URLs found in links.txt")
    exit(0)
else:
    print(f"Found {len(TARGET_URLS)} URLs to process.")
    
run_pipeline(TARGET_URLS)


