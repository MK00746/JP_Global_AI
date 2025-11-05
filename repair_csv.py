# repair_csv.py
import re
import pandas as pd
from pathlib import Path

CSV_PATH = Path("uploads/detections.csv")

def extract_number_from_str(s):
    # Try to find a number in the string
    if pd.isna(s):
        return 0
    if isinstance(s, (int, float)):
        return int(s)
    s = str(s)
    m = re.search(r"(\d+)", s)
    if m:
        return int(m.group(1))
    return 0

def repair():
    df = pd.read_csv(CSV_PATH)
    # If count column contains weird strings, extract number
    df['count'] = df['count'].apply(extract_number_from_str).astype(int)
    df.to_csv(CSV_PATH, index=False)
    print("Repaired CSV saved.")

if __name__ == "__main__":
    repair()
