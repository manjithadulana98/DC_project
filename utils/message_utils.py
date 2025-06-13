def format_message(msg):
    length = len(msg) + 5  # space + 4-digit length
    return f"{length:04} {msg}"

def parse_message(msg):
    return msg[5:]  # Remove length prefix