import re
import os

filepath = "runner/national_suitability_report.html"
with open(filepath, "r", encoding="utf-8") as f:
    html = f.read()

print("File:", filepath)
print("Bytes:", len(html))

scripts = re.findall(r'<script[^>]*src=[\'"]([^\'"]+)[\'"]', html)
print("\nScript srcs in national_suitability_report.html:")
for s in scripts:
    print(" ", s)

links = re.findall(r'<link[^>]*href=[\'"]([^\'"]+)[\'"]', html)
print("\nCSS/Font links in national_suitability_report.html:")
for l in links:
    print(" ", l)
