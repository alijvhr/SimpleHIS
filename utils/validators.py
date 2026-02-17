"""Validation utilities"""

def validate_iranian_national_id(national_id: str) -> bool:
    """
    Validate Iranian national ID (10 digits with checksum).
    Returns True if valid, False otherwise.
    """
    # Remove any non-digit characters
    national_id = ''.join(filter(str.isdigit, national_id))
    
    # Must be exactly 10 digits
    if len(national_id) != 10:
        return False
    
    # Check if all digits are the same (invalid)
    if len(set(national_id)) == 1:
        return False
    
    # Calculate checksum
    check_sum = 0
    for i in range(9):
        check_sum += int(national_id[i]) * (10 - i)
    
    remainder = check_sum % 11
    check_digit = int(national_id[9])
    
    # Validate checksum
    if remainder < 2:
        return check_digit == remainder
    else:
        return check_digit == (11 - remainder)


ALLOWED_IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}
ALLOWED_IMAGE_MIMETYPES = {
    'image/jpeg', 'image/png', 'image/gif', 'image/bmp', 'image/webp'
}
MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10 MB

def validate_image_file(filename: str, content_type: str, file_size: int) -> tuple[bool, str]:
    """
    Validate image file.
    Returns (is_valid, error_message)
    """
    import os
    
    # Check file extension using os.path.splitext for reliability
    ext = os.path.splitext(filename)[1].lower()
    if not ext or ext not in ALLOWED_IMAGE_EXTENSIONS:
        return False, "فقط فایل‌های تصویری مجاز هستند (JPG, PNG, GIF, BMP, WEBP)"
    
    # Check MIME type
    if content_type not in ALLOWED_IMAGE_MIMETYPES:
        return False, "نوع فایل نامعتبر است"
    
    # Check file size
    if file_size > MAX_IMAGE_SIZE:
        return False, f"حجم فایل نباید بیشتر از {MAX_IMAGE_SIZE // (1024*1024)} مگابایت باشد"
    
    return True, ""
