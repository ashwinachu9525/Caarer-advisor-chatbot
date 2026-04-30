from PyPDF2 import PdfReader
import pdfplumber
import docx
import pytesseract
from PIL import Image
import io


class DocumentService:

    @staticmethod
    def extract_text(file_obj, filename: str) -> str:
        ext = filename.lower().split('.')[-1]

        try:
            if ext == 'pdf':
                return DocumentService._extract_pdf(file_obj)

            elif ext == 'docx':
                return DocumentService._extract_docx(file_obj)

            elif ext == 'txt':
                return file_obj.read().decode('utf-8', errors='ignore')

            else:
                raise ValueError("Unsupported file format.")

        except Exception as e:
            print(f"Extraction Error: {e}")
            return f"Error extracting document: {str(e)}"

    # ---------------- PDF HANDLING ----------------
    @staticmethod
    def _extract_pdf(file_obj):
        text = ""

        # 🔹 Reset pointer (important)
        file_obj.seek(0)

        # ---------- 1. Try PyPDF2 ----------
        try:
            reader = PdfReader(file_obj)
            text = "\n".join(
                [page.extract_text() or "" for page in reader.pages]
            ).strip()

            if text:
                return text
        except Exception as e:
            print(f"PyPDF2 failed: {e}")

        # 🔹 Reset pointer again
        file_obj.seek(0)

        # ---------- 2. Try pdfplumber ----------
        try:
            with pdfplumber.open(file_obj) as pdf:
                text = "\n".join(
                    [page.extract_text() or "" for page in pdf.pages]
                ).strip()

            if text:
                return text
        except Exception as e:
            print(f"pdfplumber failed: {e}")

        # 🔹 Reset pointer again
        file_obj.seek(0)

        # ---------- 3. OCR fallback (for scanned PDFs) ----------
        try:
            return DocumentService._extract_pdf_with_ocr(file_obj)
        except Exception as e:
            print(f"OCR failed: {e}")

        return "⚠️ Unable to extract text from PDF."

    # ---------------- OCR METHOD ----------------
    @staticmethod
    def _extract_pdf_with_ocr(file_obj):
        import fitz  # PyMuPDF

        text = ""
        file_bytes = file_obj.read()

        pdf = fitz.open(stream=file_bytes, filetype="pdf")

        for page in pdf:
            pix = page.get_pixmap()
            img = Image.open(io.BytesIO(pix.tobytes()))

            text += pytesseract.image_to_string(img) + "\n"

        return text.strip()

    # ---------------- DOCX ----------------
    @staticmethod
    def _extract_docx(file_obj):
        doc = docx.Document(file_obj)
        return "\n".join([para.text for para in doc.paragraphs])