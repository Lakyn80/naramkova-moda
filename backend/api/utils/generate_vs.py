from datetime import datetime

def generate_vs():
    """Vygeneruje variabilní symbol ve formátu YYYYDDMMHHMM."""
    return datetime.now().strftime("%Y%d%m%H%M")
