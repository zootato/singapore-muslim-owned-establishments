import json
import sys
import csv
from typing import Any


def to_text(value: Any) -> str:
    if value is None:
        return ''
    if isinstance(value, list):
        return ' | '.join(str(x) for x in value)
    if isinstance(value, dict):
        return json.dumps(value, ensure_ascii=False)
    return str(value)


def convert(in_path: str, out_path: str):
    with open(in_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    headers = [
        'name', 'url', 'category', 'category_type', 'address',
        'latitude', 'longitude', 'telephone', 'email', 'price_range',
        'opening_hours', 'same_as', 'tags', 'description'
    ]

    with open(out_path, 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(headers)
        for item in data:
            row = [to_text(item.get(h, '')) for h in headers]
            w.writerow(row)


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print('Usage: json_to_csv.py input.json output.csv')
        sys.exit(2)
    convert(sys.argv[1], sys.argv[2])
