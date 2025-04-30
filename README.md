# Data Harvesting & Structuring

## Requirements
Install dependencies using pip:

```bash
pip install -r requirements.txt
```

**System Dependencies:**
- [Poppler](http://blog.alivate.com.au/poppler-windows/) (for `pdf2image`) (IMPORTANT)
    - Installation - ```apt-get install -y poppler-utils```

- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract)



Make sure the `tesseract` command is in your PATH.

---

## Usage

### 1. Customize Target URLs
Add links to be scraped in the `links.txt`

### 2. Run the Pipeline
```bash
python main.py
```

This will:
- Crawl all target URLs
- Download all supported files
- Extract metadata and content
- Save HTMLs and PDFs in `downloads/`
- Output structured JSON in `json_output/`


---

## Output Structure
Each document results in a JSON file like this:
```json
{
  "site": "archive.org",
  "document_id": "doc1234",
  "title": "Some Book",
  "authors": ["First Last"],
  "pub_year": "1998",
  "language": "Sanskrit",
  "download_url": "https://.../file.pdf",
  "checksum": "a1b2c3...",
  "scraped_at": "2025-04-30T13:45:00Z",
  "content": "Full extracted text..."
}
```

---

