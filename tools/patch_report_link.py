with open('runner/national_suitability_report.html', 'r', encoding='utf-8') as f:
    s = f.read()

s = s.replace('href="data_verification_technical_report.html"', 'href="docs/qa/QA_Report_20260902.html"')

with open('runner/national_suitability_report.html', 'w', encoding='utf-8') as f:
    f.write(s)

with open('runner/build_suitability_report.py', 'r', encoding='utf-8') as f:
    s2 = f.read()

s2 = s2.replace('href="data_verification_technical_report.html"', 'href="docs/qa/QA_Report_20260902.html"')

with open('runner/build_suitability_report.py', 'w', encoding='utf-8') as f:
    f.write(s2)

print("Patched successfully")
