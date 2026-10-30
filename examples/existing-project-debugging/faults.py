"""Isolated historical bug; not imported by the working application."""
import csv
import io

def drops_last_row(text):
    rows=list(csv.DictReader(io.StringIO(text)))
    return [r for r in rows[:-1] if r['status']=='active']
