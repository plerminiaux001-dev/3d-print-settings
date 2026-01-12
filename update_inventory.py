import os
import re
import pandas as pd
import shutil
from datetime import datetime

# --- CONFIGURATION (GITHUB PATHS) ---
CSV_FILE = 'Filament Inventory - Inventory.csv'
INPUT_FOLDER = 'To_Inventory'
ARCHIVE_FOLDER = 'Inventoried'
HTML_FILE = 'index.html'

def log(message):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")

def get_filament_data(gcode_path):
    results = []
    try:
        with open(gcode_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        # Extract Weight
        weight_match = re.search(r"; filament used \[g\] = (.+)", content)
        # Extract Profile Name
        name_match = re.search(r'; filament_settings_id = (.+)', content)
        
        if weight_match and name_match:
            usage = float(weight_match.group(1).strip().split(',')[0])
            name = name_match.group(1).replace('"', '').strip()
            results.append((name, usage))
            log(f"Found in G-code: {name} used {usage}g")
    except Exception as e:
        log(f"Error reading {gcode_path}: {e}")
    return results

def generate_html(df):
    # Create the inventory table string
    inventory_rows = ""
    for _, row in df.sort_values('Weight (g)').iterrows():
        color = "#d9534f" if row['Weight (g)'] < 250 else "#6b8e23"
        inventory_rows += f"<tr><td>{row['Filament Name']}</td><td>{row['Color']}</td><td style='color:{color}; font-weight:bold;'>{row['Weight (g)']}g</td><td>{row['Profile Name']}</td></tr>"
    
    table_html = f"<table><thead><tr><th>Filament</th><th>Color</th><th>Stock</th><th>Profile</th></tr></thead><tbody>{inventory_rows}</tbody></table>"

    # 1. Read the Template
    with open('template.html', 'r', encoding='utf-8') as f:
        content = f.read()

    # 2. Inject the data into placeholders
    content = content.replace('', table_html)
    content = content.replace('', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

    # 3. Save as the final index.html
    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(content)
        
def main():
    log("--- Starting Inventory Update ---")
    if not os.path.exists(INPUT_FOLDER): os.makedirs(INPUT_FOLDER)
    
    files = [f for f in os.listdir(INPUT_FOLDER) if f.lower().endswith('.gcode')]
    df = pd.read_csv(CSV_FILE)
    
    if not files:
        log("No files in To_Inventory. Updating HTML only.")
        generate_html(df)
        return

    for filename in files:
        log(f"Processing: {filename}")
        updates = get_filament_data(os.path.join(INPUT_FOLDER, filename))
        for p_name, usage in updates:
            mask = df['Profile Name'] == p_name
            if mask.any():
                df.loc[mask, 'Weight (g)'] = round(df.loc[mask, 'Weight (g)'].iloc[0] - usage, 2)
                log(f"   Success: {p_name} updated.")
            else:
                log(f"   Warning: Profile '{p_name}' not found in CSV.")
        
        if not os.path.exists(ARCHIVE_FOLDER): os.makedirs(ARCHIVE_FOLDER)
        shutil.move(os.path.join(INPUT_FOLDER, filename), os.path.join(ARCHIVE_FOLDER, filename))
    
    df.to_csv(CSV_FILE, index=False)
    generate_html(df)
    log("Update complete.")

if __name__ == "__main__":
    main()
