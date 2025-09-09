from datetime import datetime, timedelta


def format_booking_message(data):
    # Extract fields
    patient = data.get("patient")
    age = data.get("age")
    service = data.get("service")
    doctor = data.get("doctor")
    date_str = data.get("date")  # 'YYYY-MM-DD'
    time_str = data.get("time")  # e.g. '14:30' or '11:00 AM'

    # Handle missing date/time gracefully
    if not date_str:
        return "Booking information is incomplete: missing date."

    booking_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    today = datetime.today().date()
    tomorrow = today + timedelta(days=1)

    # Human-friendly date label
    if booking_date == today:
        day_label = "today"
    elif booking_date == tomorrow:
        day_label = "tomorrow"
    else:
        day_label = booking_date.strftime("on %A, %B %d")  # e.g., "on Friday, August 15"

    # Build natural message depending on presence of doctor vs service type
    if doctor:
        res_text = (f"Okay, I've booked the earliest available slot with {doctor} "
                    f"for {service} at {time_str} {day_label}. "
                    "Please be on time. Is there anything else I can help with?")
    else:
        res_text = (f"Okay, your {service} has been scheduled at {time_str} {day_label}. "
                    "Please be on time. Do you need help with anything else?")

    return res_text
