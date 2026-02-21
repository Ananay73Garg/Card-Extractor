import random
import string
import re
import cv2
import numpy as np
import pytesseract
import mysql.connector
import ollama
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from PIL import Image
from io import BytesIO
from pdf2image import convert_from_bytes

app = FastAPI()

db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="root1234",
    database="card_system"
)

def generate_code(letter="U"):
    return letter + ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))

def generate_unique_code(letter="U"):
    cursor = db.cursor()
    while True:
        code = generate_code(letter)
        cursor.execute("SELECT id FROM card_records WHERE id=%s", (code,))
        if not cursor.fetchone():
            return code

def check_blur(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    return cv2.Laplacian(gray, cv2.CV_64F).var()

def extract_text(image):
    return pytesseract.image_to_string(image)

def clean_text(text):
    lines = text.split("\n")
    filtered = [l.strip() for l in lines if re.search(r'\d', l)]
    return "\n".join(filtered)

def extract_card_details(text):
    aadhaar_pattern = r"\b\d{4}\s\d{4}\s\d{4}\b"
    pan_pattern = r"\b[A-Z]{5}\d{4}[A-Z]\b"
    dob_pattern = r"\b\d{2}/\d{2}/\d{4}\b"
    card_number = None
    card_type = None
    if re.search(aadhaar_pattern, text):
        card_number = re.search(aadhaar_pattern, text).group()
        card_type = "Aadhaar"
    elif re.search(pan_pattern, text):
        card_number = re.search(pan_pattern, text).group()
        card_type = "PAN"
    dob = re.search(dob_pattern, text)
    dob = dob.group() if dob else None
    return card_type, card_number, dob

def extract_name_with_ollama(text):
    response = ollama.chat(
        model="llama3:8b-instruct-q4_0",
        messages=[{"role": "user", "content": f"Extract only the person's full name from this text:\n{text}\nOnly return the name.Dont give any other text other than the name."}],
        stream=False
    )
    return response["message"]["content"].strip()

def ensure_threshold_row():
    cursor = db.cursor()
    cursor.execute("SELECT COUNT(*) FROM failure_logs WHERE reason='thresholds'")
    if cursor.fetchone()[0] == 0:
        cursor.execute(
            "INSERT INTO failure_logs (id, blur_score, brightness_std, mean_intensity, file_size, reason) VALUES (%s,%s,%s,%s,%s,%s)",
            ("FTHRS", 50, 50, 200, 2*1024*1024, "thresholds")
        )
        db.commit()

ensure_threshold_row()

@app.post("/extract")
async def extract_card(file: UploadFile = File(...)):
    contents = await file.read()
    if len(contents) > 2*1024*1024:
        user_id = generate_unique_code("F")
        cursor = db.cursor()
        cursor.execute(
            "INSERT INTO failure_logs (id, file_size, reason) VALUES (%s,%s,%s)",
            (user_id, len(contents), "file too large")
        )
        db.commit()
        raise HTTPException(status_code=400, detail="File too large")
    if file.filename.lower().endswith(".pdf"):
        images = convert_from_bytes(contents)
        if not images:
            raise HTTPException(status_code=400, detail="PDF could not be converted")
        image = images[0].convert("RGB")
    else:
        image = Image.open(BytesIO(contents)).convert("RGB")
    image_np = np.array(image)
    image_cv = cv2.cvtColor(image_np, cv2.COLOR_RGB2BGR)
    image_cv = cv2.resize(image_cv, (1000, 600))
    if check_blur(image_cv) < 50:
        user_id = generate_unique_code("F")
        cursor = db.cursor()
        cursor.execute(
            "INSERT INTO failure_logs (id, blur_score, reason) VALUES (%s,%s,%s)",
            (user_id, check_blur(image_cv), "image blurry")
        )
        db.commit()
        raise HTTPException(status_code=400, detail="Image is too blurry")
    raw_text = extract_text(image_cv)
    cleaned_text = clean_text(raw_text)
    card_type, card_number, dob = extract_card_details(cleaned_text)
    if not card_number:
        user_id = generate_unique_code("F")
        cursor = db.cursor()
        cursor.execute(
            "INSERT INTO failure_logs (id, reason) VALUES (%s,%s)",
            (user_id, "card number not detected")
        )
        db.commit()
        raise HTTPException(status_code=400, detail="Card number not detected")
    name = extract_name_with_ollama(raw_text)
    user_id = generate_unique_code("U")
    cursor = db.cursor()
    cursor.execute(
        "INSERT INTO card_records (id, name, card_type, card_number, dob) VALUES (%s,%s,%s,%s,%s)",
        (user_id, name, card_type, card_number, dob)
    )
    db.commit()
    return {"user_id": user_id, "name": name, "card_type": card_type, "card_number": card_number, "dob": dob}

@app.post("/display")
def display_entry(user_id: str = Form(...)):
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM card_records WHERE id=%s", (user_id,))
    result = cursor.fetchone()
    if not result:
        raise HTTPException(status_code=404, detail="Not found")
    return result

@app.post("/delete")
def delete_entry(user_id: str = Form(...)):
    cursor = db.cursor()
    cursor.execute("DELETE FROM card_records WHERE id=%s", (user_id,))
    db.commit()
    if cursor.rowcount == 0:
        raise HTTPException(status_code=404, detail="Not found")
    return {"message": "Deleted successfully"}

@app.get("/all")
def get_all():
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM card_records")
    return cursor.fetchall()

@app.get("/logger")
def get_logger():
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM failure_logs ORDER BY id ASC")
    return cursor.fetchall()