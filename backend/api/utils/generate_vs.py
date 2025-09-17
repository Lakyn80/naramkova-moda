from datetime import datetime

def generate_vs():
    """Vygeneruje variabilní symbol ve formátu YYDDMMHHMM."""
    return datetime.now().strftime("%Y%d%m%H%M")
