📄 Milestone 1: Document Ingestion & OCR System (Enhanced)
Web Application ONLY – Receipt OCR Dashboard (Structured OCR Output)

This project is a Flask-based Web Application that allows users to upload Receipt / Invoice images or PDFs and extract text using Tesseract OCR.  
It includes image preprocessing, OCR confidence calculation, and structured receipt extraction (Store name, Date, Time, Items, Subtotal, Tax, Total, Payment type, Card info).

🚀 Features

✅ Upload receipts in JPG / PNG / PDF format  
✅ Auto PDF → Image conversion (first page only)  
✅ Image preprocessing using OpenCV:
- Resize + Denoising
- Gray conversion
- CLAHE enhancement
- Adaptive thresholding

✅ OCR extraction using pytesseract
✅ Displays:
- Original Image
- Processed Image
- OCR Confidence %
- Word Count
- Structured Receipt Output

✅ Extracts structured details:
- Store Name
- Date
- Time
- Items with qty & price
- Subtotal / Tax / Total
- Payment type (Cash/Card)
- Card last digits (if present)

🛠️ Tech Stack

- **Python**
- **Flask**
- **OpenCV**
- **Tesseract OCR**
- **pdf2image**
- **HTML + CSS + JS (frontend inside Flask)**

📂 Project Structure

Milestone1-OCR/
│── app.py
│── uploads/          # Uploaded files stored here
│── processed/        # Preprocessed outputs stored here
│── README.md

⚙️ Requirements
✅ Install Dependencies

pip install flask opencv-python pillow pytesseract pdf2image numpy werkzeug

🧩 External Installations Required
 
1️⃣ Install Tesseract OCR

Download & install from:

[https://github.com/tesseract-ocr/tesseract](https://github.com/tesseract-ocr/tesseract)

Then set path inside code:

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

2️⃣ Install Poppler (Required for PDF support)

To convert PDF → images, Poppler is required.

✅ Install Poppler for Windows and set path:

poppler_path=r"C:\Users\ADMIN\AppData\Local\Microsoft\WinGet\Packages\...\poppler-25.07.0\Library\bin"

▶️ How to Run

Run the Flask server:

python app.py

Then open in browser:

http://localhost:5000

🧪 Usage Steps

1. Open the web dashboard
2. Upload a receipt (`.jpg / .png / .pdf`)
3. Click Process
4. You will get:

   * Original preview
   * Preprocessed preview
   * Extracted Structured OCR text
   * Confidence score

📌 Output Example

Structured OCR output includes:

```
STORE NAME
ABC MART
--------------------
DATE: 12/01/2026
TIME: 10:45 AM
--------------------
ITEMS
MILK | 1 | 25.00
BREAD | 2 | 50.00
--------------------
SUBTOTAL: 75.00
TAX: 3.00
TOTAL: 78.00
--------------------
PAYMENT: CARD
CARD: 1234
```
✅ Milestone 1 Objectives Completed

✔ File Upload Interface
✔ Document ingestion support (Image/PDF)
✔ Image preprocessing pipeline
✔ OCR extraction engine
✔ Structured output for receipts
✔ Confidence & word count statistics
✔ Web dashboard view for results

🔐 Notes

* For PDFs, only the **first page** is processed.
* The OCR output depends on image quality.
* Preprocessing improves OCR accuracy significantly.

