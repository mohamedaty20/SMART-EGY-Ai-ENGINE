"""
services/pdf_service.py

QR code + shared PDF helpers.
"""
import io


def generate_qr_code(data: str) -> io.BytesIO:
    """
    Return a BytesIO containing a PNG QR code of the given data.
    Caller is responsible for reading from the returned buffer.
    """
    import qrcode
    img = qrcode.make(data)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf
