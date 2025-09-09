import re

def get_booking_data(text):
    # Flexible regex pattern allowing Service and optional Doctor
    pattern = r"""
    BOOKING_CONFIRMATION:                       
    \s*[-–—]?\s*                                
    Patient:\s*(.*?)[,\-]\s*Age\s*(\d+)         # Patient name and age
    \s*[-–—]?\s*Service:\s*(.*?)                # Capture Service
    (?:\s*[-–—]?\s*Doctor:\s*(.*?))?            # Optional Doctor
    \s*[-–—]?\s*Date:\s*([\d]{4}-\d{2}-\d{2})   # Capture Date
    \s*[-–—]?\s*Time:\s*([\d]{1,2}:\d{2}\s*[APMapm]{0,2})? # Capture Time (optional AM/PM)
    """

    match = re.search(pattern, text, re.VERBOSE | re.IGNORECASE)
    if match:
        patient_name = match.group(1).strip()
        age = match.group(2).strip()
        service = match.group(3).strip()
        doctor_name = match.group(4).strip() if match.group(4) else None
        date = match.group(5).strip()
        time = match.group(6).strip() if match.group(6) else None

        booking_data = {
            "patient": patient_name,
            "age": age,
            "service": service,
            "doctor": doctor_name,
            "date": date,
            "time": time
        }

        print(booking_data)
        return booking_data
    else:
        print("No booking data found.")
        return None