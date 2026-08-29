import os
import sys
import base64

def main():
    log_path = r"c:\Projects\aura_siting_crafter\national.log"
    output_path = r"C:\Users\corea\.gemini\antigravity-ide\brain\e8317368-d5fd-4838-913c-23e38fa1b871\national_suitability.png"
    
    if not os.path.exists(log_path):
        print(f"Log path {log_path} not found")
        return
        
    b64_lines = []
    in_b64 = False
    
    with open(log_path, 'r', encoding='utf-16') as f:
        for line in f:
            line_str = line.strip()
            if "===START_B64_IMAGE===" in line_str:
                in_b64 = True
                continue
            elif "===END_B64_IMAGE===" in line_str:
                in_b64 = False
                break
            elif in_b64:
                # Remove line number prefix if present (e.g. "123: ...")
                if ":" in line_str:
                    parts = line_str.split(":", 1)
                    # check if the first part is a number
                    if parts[0].strip().isdigit():
                        line_str = parts[1].strip()
                b64_lines.append(line_str)
                
    if not b64_lines:
        print("No base64 image content found in logs.")
        return
        
    b64_data = "".join(b64_lines)
    # Remove any trailing spaces/newlines
    b64_data = b64_data.replace(" ", "").replace("\n", "").replace("\r", "")
    
    try:
        img_bytes = base64.b64decode(b64_data)
        with open(output_path, 'wb') as img_f:
            img_f.write(img_bytes)
        print(f"Successfully extracted image to {output_path}")
    except Exception as e:
        print(f"Failed to decode base64 image: {e}")

if __name__ == "__main__":
    main()
