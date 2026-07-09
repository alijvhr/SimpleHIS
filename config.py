"""Configuration settings"""

# Admission pricing
ADMISSION_PRICES = {
    'doctor': 50000,
    'laboratory': 0,
    'radiology': 200000
}

def get_admission_price(admission_type: str) -> int:
    """Get price for an admission type"""
    return ADMISSION_PRICES.get(admission_type, 0)
