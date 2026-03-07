# AI Document Filler

## Overview
AI Document Filler is a FastAPI-based backend system that extracts information from Indian identity cards such as Aadhaar and PAN cards using OCR and AI-based name extraction.

The system processes uploaded images or PDFs, validates their quality, extracts key information, and stores the results in a MySQL database. It also maintains failure logs for debugging and monitoring when documents fail validation.

---

# Features

## Document Upload
Users can upload:
- Image files (JPG, PNG)
- PDF documents

PDF files are automatically converted to images before processing.

---

## Image Validation
Before extracting information, the system performs several checks:

- File size validation (maximum 2MB)
- Blur detection using OpenCV Laplacian variance
- Image resizing for better OCR accuracy

If validation fails, the request is logged in the `failure_logs` table.

---

## OCR Text Extraction
Text is extracted using Tesseract OCR.  
The system cleans the extracted text to remove irrelevant lines and focuses on lines containing numbers to improve card detection accuracy.

---

## Card Detail Detection
Regex pattern matching is used to identify important details.

| Field | Detection Pattern |
|------|------|
| Aadhaar Number | XXXX XXXX XXXX |
| PAN Number | ABCDE1234F |
| Date of Birth | DD/MM/YYYY |

---

## AI Name Extraction (Development Version)
The development version of this project uses **Ollama with the Llama3 model** to extract the person's full name from the OCR text.

This allows the system to identify the correct name even when OCR produces noisy or unstructured text.

---

## Unique User ID Generation
Each successful record is assigned a unique ID.

Example:
Failure logs use IDs starting with:
---

# Database Structure

## card_records

| Column | Description |
|------|------|
| id | Generated unique user ID |
| name | Extracted name |
| card_type | Aadhaar or PAN |
| card_number | Card number |
| dob | Date of birth |

---

## failure_logs

Stores information about failed processing attempts.

| Column | Description |
|------|------|
| id | Failure ID |
| blur_score | Image blur metric |
| brightness_std | Image brightness |
| mean_intensity | Image intensity |
| file_size | Uploaded file size |
| reason | Failure reason |

---

# API Endpoints

## Extract Card Details

#POST /extract
Uploads a card image or PDF and extracts card information.

Example Response:

json
{
  "user_id": "U3F9K2",
  "name": "Rohan Sharma",
  "card_type": "Aadhaar",
  "card_number": "1234 5678 9123",
  "dob": "12/08/1995"
}

## Display Entry
# POST /display
Example input : user_id=U3F9K2

## Delete Entry
# POST /delete
Deletes a stored record from the database.

## Get All Records
# GET /all
Returns all stored card records.

## Get Failure Logs
# Get /logger
Returns all failure logs for monitoring and debugging.

---

## Deployment Version

The deployed production version of this system does **not use the Ollama AI model**.

Instead, the **user manually inputs their name along with the card upload**, while the system automatically extracts:

- Card Type  
- Card Number  
- Date of Birth  

This approach removes the dependency on running a local AI model on the server.

---

## Tech Stack

- **FastAPI** – Backend framework  
- **OpenCV** – Image processing and blur detection  
- **Tesseract OCR** – Text extraction  
- **Ollama + Llama3** – AI name extraction (development version)  
- **MySQL** – Database storage  
- **PIL / pdf2image** – Image and PDF processing  

---

## Possible Future Improvements

- Automatic card boundary detection and cropping  
- Improved OCR preprocessing  
- Multi-card support  
- Face detection for identity verification  
- Cloud AI inference instead of local models
