import os
import re
import pandas as pd
import shutil
from datetime import datetime

# Paths
CSV_FILE = 'Filament Inventory - Inventory.csv'
INPUT_FOLDER = 'To_Inventory'
ARCHIVE_FOLDER = 'Inventoried'
TEMPLATE_FILE = 'template.html'
HTML_FILE = 'index.html'

def log(message):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")

def generate_html(df):
    # build table rows
    rows = ""
    for _, row in df.sort_values('Weight (g)').iterrows():
        color = "#d9534f" if row['Weight (g)'] < 250 else "#6b8e23"
        rows += f"<tr><td>{row['Filament Name']}</td><td>{row['Color']}</td><td style='color:{color}; font-weight:bold;'>{row['Weight (g)']}g</td><td>{row['Profile Name']}</td></tr>"
    
    table_html = f"<table><thead><tr><th>Filament</th><th>Color</th><th>Stock</th><th>Profile</th></tr></thead><tbody>{rows}</tbody></table>"

    if not os.path.exists(TEMPLATE_FILE):
        log("Template.html missing!")
        return

    with open(TEMPLATE_FILE, 'r', encoding='utf-8') as f:
        content = f.read()

    # Inject data
    content = content.replace('', table_html)
    content = content.replace('', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

    with open(HTML_FILE, 'w', encoding='utf-8') as f:
        f.write(content)
    log(f"Generated {HTML_FILE} ({len(content)/1024:.2f} KB)")

def main():
    log("--- Sync Started ---")
    if not os.path.exists(INPUT_FOLDER): os.makedirs(INPUT_FOLDER)
    files = [f for f in os.listdir(INPUT_FOLDER) if f.lower().endswith('.gcode')]
    
    # Reload CSV
    df = pd.read_csv(CSV_FILE)
    
    if files:
        for filename in files:
            path = os.path.join(INPUT_FOLDER, filename)
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                # Read only the first 100,000 characters to find headers (saves memory/prevents bugs)
                chunk = f.read(100000) 
                
                # FIXED REGEX: [^\r\n]+ means "stop at the first newline"
                w_match = re.search(r"; filament used \[g\] = ([^\r\n]+)", chunk)
                n_match = re.search(r'; filament_settings_id = ([^\r\n]+)', chunk)
                
                if w_match and n_match:
                    usage = float(w_match.group(1).split(',')[0])
                    # Safety cap: Keep only the first 100 chars of the profile name
                    name = n_match.group(1).replace('"', '').strip()[:100] 
                    
                    mask = df['Profile Name'] == name
                    if mask.any():
                        df.loc[mask, 'Weight (g)'] = round(df.loc[mask, 'Weight (g)'].iloc[0] - usage, 2)
                        log(f"Processed {filename}: -{usage}g")
            
            if not os.path.exists(ARCHIVE_FOLDER): os.makedirs(ARCHIVE_FOLDER)
            shutil.move(path, os.path.join(ARCHIVE_FOLDER, filename))
        
        df.to_csv(CSV_FILE, index=False)
    
    generate_html(df)

if __name__ == "__main__":
    main()
