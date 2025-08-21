# import re
#
# text = """Okay, I have a slot available with Dr. Fatima Siddiqui for Abhash, age 2.  BOOKING_CONFIRMATION: -
# Patient: Abhash, Age 2 - Doctor: Dr. Fatima Siddiqui (Pediatrician) - Date: 2024-07-03 - Time: 11:00"""
#
# pattern = r"BOOKING_CONFIRMATION:\s*-\s*Patient:\s*(.*?),\s*Age\s*(\d+)\s*-\s*Doctor:\s*(.*?)\s*-\s*Date:\s*([\d-]+)\s*-\s*Time:\s*([\d:]+)"
#
# match = re.search(pattern, text)
#
# if match:
#     patient_name = match.group(1)
#     age = match.group(2)
#     doctor_name = match.group(3)
#     date = match.group(4)
#     time = match.group(5)
#     print({
#         "patient": patient_name,
#         "age": age,
#         "doctor": doctor_name,
#         "date": date,
#         "time": time
#     })

import re
from datetime import datetime


def get_booking_data(text):
    # Flexible regex pattern
    pattern = r"""
    BOOKING_CONFIRMATION:              # match the literal text
    \s*[-–—]?\s*                       # optional dash and spaces
    Patient:\s*(.*?)[,\-]\s*Age\s*(\d+) # capture patient name, then age
    \s*[-–—]?\s*Doctor:\s*(.*?)         # capture doctor name
    \s*[-–—]?\s*Date:\s*([\d]{4}-\d{2}-\d{2}) # capture date
    \s*[-–—]?\s*Time:\s*([\d]{1,2}:\d{2})     # capture time
    """

    match = re.search(pattern, text, re.VERBOSE | re.IGNORECASE)

    if match:
        patient_name = match.group(1).strip()
        age = match.group(2).strip()
        doctor_name = match.group(3).strip()
        date = match.group(4).strip()
        time = match.group(5).strip()

        # formatted_time = str(datetime.strptime(date, "%Y-%m-%d").strftime("%Y-%m-%d"))

        booking_data = {
            "patient": patient_name,
            "age": age,
            "doctor": doctor_name,
            "date": date,
            "time": time
        }

        print(booking_data)
        return booking_data