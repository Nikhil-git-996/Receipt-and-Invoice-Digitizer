# Milestone 1: Document Ingestion & OCR System (Enhanced)
# Web Application ONLY – Receipt OCR Dashboard (Structured OCR Output)

import os
import cv2
import re
import numpy as np
from PIL import Image
import pytesseract
from pdf2image import convert_from_path
from datetime import datetime
from werkzeug.utils import secure_filename
from flask import Flask, request, jsonify, render_template_string
import base64

# ---------------- TESSERACT PATH ----------------
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# =================================================
# IMAGE PREPROCESSOR (UNCHANGED)
# =================================================
class ImagePreprocessor:
    def preprocess(self, path):
        img = cv2.imread(path)
        if img is None:
            return None, None

        img = cv2.resize(img, (1200, int(img.shape[0] * 1200 / img.shape[1])))
        den = cv2.fastNlMeansDenoisingColored(img, None, 10, 10, 7, 21)
        gray = cv2.cvtColor(den, cv2.COLOR_BGR2GRAY)

        clahe = cv2.createCLAHE(3.0, (8, 8))
        enhanced = clahe.apply(gray)

        binary = cv2.adaptiveThreshold(
            enhanced, 255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY, 21, 10
        )

        return enhanced, binary


# =================================================
# OCR ENGINE (STABLE + FIXED)
# =================================================
class OCREngine:
    def extract(self, image):

        pil = Image.fromarray(image)

        raw_text = pytesseract.image_to_string(
            pil, config="--oem 3 --psm 6"
        )

        data = pytesseract.image_to_data(
            pil,
            config="--oem 3 --psm 6",
            output_type=pytesseract.Output.DICT
        )

        # ---------------- CONFIDENCE ----------------
        confs = [float(c) for c in data["conf"] if c != "-1"]
        confidence = round(sum(confs) / len(confs), 2) if confs else 0

        # ---------------- LINE GROUPING ----------------
        lines = {}
        for i in range(len(data["text"])):
            txt = data["text"][i].strip()
            if not txt:
                continue
            ln = data["line_num"][i]
            x = data["left"][i]
            lines.setdefault(ln, []).append({"text": txt, "x": x})

        full_text = raw_text.upper()

        out = {
            "store_name": "",
            "date": "",
            "time": "",
            "items": [],
            "subtotal": "",
            "tax": "",
            "total": "",
            "payment": "CASH",
            "card": ""
        }

        # ---------------- STORE NAME ----------------
        for ln in sorted(lines):
            t = " ".join(w["text"] for w in lines[ln])
            if len(t) > 4 and not re.search(r"\d", t):
                out["store_name"] = t.title()
                break

        # ---------------- DATE ----------------
        for p in [
            r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b",
            r"\b\d{1,2}\s*(JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)\b",
            r"\b(JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)\s*\d{1,2}\b"
        ]:
            m = re.search(p, full_text)
            if m:
                out["date"] = m.group()
                break

        # ---------------- TIME ----------------
        m = re.search(r"\b\d{1,2}:\d{2}\s?(AM|PM)?\b", raw_text, re.I)
        if m:
            out["time"] = m.group()

        # ---------------- ITEMS ----------------
        for ln in lines:
            row = sorted(lines[ln], key=lambda x: x["x"])
            texts = [w["text"] for w in row]

            price = None
            for t in texts[::-1]:
                if re.match(r"\d+\.\d{2}", t):
                    price = t
                    break

            if not price:
                continue

            if any(k in " ".join(texts).upper()
                   for k in ["TOTAL", "SUB", "TAX", "AMOUNT", "NET"]):
                continue

            qty = "1"
            if re.match(r"\d+", texts[0]):
                qty = texts[0]
                name = " ".join(texts[1:-1])
            else:
                name = " ".join(texts[:-1])

            name = name.strip()
            if len(name) < 2:
                continue

            out["items"].append(f"{name} | {qty} | {price}")

        # ---------------- SAFE AMOUNT EXTRACTION ----------------
        def amt(pattern):
            m = re.search(
                rf"(?:{pattern})\s*[:\-]?\s*\$?(\d+\.\d{{2}})",
                full_text,
                re.I
            )
            if not m:
                return None
            try:
                return float(m.group(1))
            except:
                return None

        subtotal = amt("SUBTOTAL|NET TOTAL|AMOUNT|RUPEES")
        tax = amt("TAX")
        total = amt(r"(?<!SUB)\bTOTAL\b")

        # ---------------- FINAL AMOUNT LOGIC ----------------
        if subtotal is not None and tax is not None:
            total = round(subtotal + tax, 2)
        elif total is not None and tax is not None:
            subtotal = round(total - tax, 2)

        out["subtotal"] = f"{subtotal:.2f}" if isinstance(subtotal, float) else ""
        out["tax"] = f"{tax:.2f}" if isinstance(tax, float) else ""
        out["total"] = f"{total:.2f}" if isinstance(total, float) else ""

        # ---------------- PAYMENT ----------------
        if re.search(r"VISA|MASTER|CARD", full_text):
            out["payment"] = "CARD"

        m = re.search(r"\*{2,}(\d{3,4})", raw_text)
        if m:
            out["card"] = m.group(1)

        return {
            "raw_text": raw_text,
            "confidence": confidence,
            "word_count": len(raw_text.split()),
            "structured": out
        }


# =================================================
# FLASK APP
# =================================================
app = Flask(__name__)
os.makedirs("uploads", exist_ok=True)
os.makedirs("processed", exist_ok=True)

pre = ImagePreprocessor()
ocr = OCREngine()

# =================================================
# ✅ FULL HTML (COMPLETE)
# =================================================
HTML = """
<!DOCTYPE html>
<html>
<head>
<title>Milestone 1: Document Ingestion & OCR</title>
<style>
body{font-family:Segoe UI;background:#eef1ff;padding:20px}
.container{background:#fff;padding:25px;border-radius:12px;max-width:1400px;margin:auto}
.header{font-size:22px;font-weight:600;color:#1f3c88;margin-bottom:15px}
.grid{display:grid;grid-template-columns:1fr 1fr 1fr;gap:20px}
.card{background:#f8f9fc;padding:20px;border-radius:10px}
.card h3{margin-bottom:10px;color:#1f3c88}
.upload{border:2px dashed #4f6bed;padding:25px;text-align:center;border-radius:10px}
button{padding:10px 20px;background:#4f6bed;color:#fff;border:none;border-radius:6px;cursor:pointer}
img{width:100%;border-radius:6px;margin-top:10px}
pre{white-space:pre-wrap;font-family:Consolas;font-size:13px}
.stat{margin-top:10px;font-weight:600}
</style>
</head>
<body>

<div class="container">
<div class="header">📄 Milestone 1: Document Ingestion & OCR</div>

<div class="grid">

<div class="card">
<h3>📁 File Upload Interface</h3>
<div class="upload">
<input type="file" id="file"><br><br>
<button onclick="upload()">Process</button>
<p id="statusMsg" style="margin-top:10px;font-weight:600;color:#1f3c88"></p>
<p style="font-size:13px;color:#666;margin-top:10px">
Supports JPG, PNG, PDF
</p>
</div>
</div>

<div class="card">
<h3>🖼️ Image Preprocessing</h3>
<b>Original</b>
<img id="orig">
<b>Processed</b>
<img id="proc">
</div>

<div class="card">
<h3>📝 OCR Text Extraction</h3>
<div class="stat">Confidence: <span id="conf">-</span>%</div>
<div class="stat">Word Count: <span id="wc">-</span></div>
<hr>
<pre id="structured">Upload a receipt to extract text</pre>
</div>

</div>
</div>

<script>
async function upload(){
 const f=document.getElementById("file").files[0];
 const status=document.getElementById("statusMsg");

 if(!f){ alert("Select a file"); return; }

 status.innerText="Upload Successful";
 let fd=new FormData();
 fd.append("file",f);

 status.innerText="Processing image...";

 let r=await fetch("/process",{method:"POST",body:fd});
 let d=await r.json();

 if(d.error){ alert(d.error); status.innerText=""; return; }

 document.getElementById("orig").src="data:image/png;base64,"+d.images.original;
 document.getElementById("proc").src="data:image/png;base64,"+d.images.processed;
 document.getElementById("conf").innerText=d.ocr.confidence;
 document.getElementById("wc").innerText=d.ocr.word_count;

 let flds=d.ocr.structured;
 document.getElementById("structured").innerText=
`STORE NAME
${flds.store_name}
--------------------
DATE: ${flds.date}
TIME: ${flds.time}
--------------------
ITEMS
${flds.items.join("\\n")}
--------------------
SUBTOTAL: ${flds.subtotal}
TAX: ${flds.tax}
TOTAL: ${flds.total}
--------------------
PAYMENT: ${flds.payment}
CARD: ${flds.card}`;

 status.innerText="Processing completed";
}
</script>
</body>
</html>
"""

@app.route("/")
def home():
    return render_template_string(HTML)

@app.route("/process", methods=["POST"])
def process():
    file = request.files.get("file")
    if not file:
        return jsonify({"error": "No file"}), 400

    name = secure_filename(file.filename)
    path = os.path.join("uploads", f"{int(datetime.now().timestamp())}_{name}")
    file.save(path)

    if path.lower().endswith(".pdf"):
        pages = convert_from_path(
            path,
            dpi=300,
            poppler_path=r"C:\Users\ADMIN\AppData\Local\Microsoft\WinGet\Packages\oschwartz10612.Poppler_Microsoft.Winget.Source_8wekyb3d8bbwe\poppler-25.07.0\Library\bin"
        )
        path = path.replace(".pdf", ".png")
        pages[0].save(path, "PNG")

    gray, binary = pre.preprocess(path)
    if gray is None:
        return jsonify({"error": "Invalid image"}), 400

    cv2.imwrite("processed/final.png", binary)
    ocr_res = ocr.extract(gray)

    def b64(p):
        _, buf = cv2.imencode(".png", cv2.imread(p))
        return base64.b64encode(buf).decode()

    return jsonify({
        "ocr": ocr_res,
        "images": {
            "original": b64(path),
            "processed": b64("processed/final.png")
        }
    })

if __name__ == "__main__":
    print("🚀 Open http://localhost:5000")
    app.run(debug=False, use_reloader=False)
