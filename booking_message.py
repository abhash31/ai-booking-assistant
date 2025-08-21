from datetime import datetime, timedelta

def format_booking_message(data):
    # Extract date and time from booking_data
    doctor = data['doctor']
    date_str = data['date']  # assuming 'YYYY-MM-DD' format
    time_str = data['time']  # assuming something like '14:30'

    # Convert date to datetime object
    booking_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    today = datetime.today().date()
    tomorrow = today + timedelta(days=1)

    # Determine human-friendly date label
    if booking_date == today:
        day_label = "today"
    elif booking_date == tomorrow:
        day_label = "tomorrow"
    else:
        day_label = booking_date.strftime("on %A, %B %d")  # e.g., "on Friday, August 15"

    # Final message
    res_text = f"Okay, I've booked the first available slot with {doctor} at {time_str} {day_label}. Please be on time. Is there anything else that I can help you with?"
    return res_text
