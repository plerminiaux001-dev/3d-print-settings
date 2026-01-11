import os
import re
import pandas as pd
import shutil
from datetime import datetime

# --- CONFIGURATION ---
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

        usage_list = []
        weight_match = re.search(r"; filament used \[g\] = (.+)", content)
        if weight_match:
            raw_nums = weight_match.group(1).strip()
            usage_list = [float(x) for x in raw_nums.split(',') if x.strip().replace('.', '', 1).isdigit()]

        name_list = []
        id_line_match = re.search(r'; filament_settings_id = (.+)', content)
        if id_line_match:
            line_text = id_line_match.group(1)
            name_list = re.findall(r'"([^"]*)"', line_text)
            if not name_list:
                name_list = [x.strip() for x in line_text.split(';')]

        for index, amount in enumerate(usage_list):
            if amount > 0:
                profile_used = name_list[index] if index < len(name_list) else (name_list[0] if name_list else "Unknown")
                results.append((profile_used, amount))
    except Exception as e:
        log(f"Error reading file: {e}")
    return results

def update_csv_and_generate_html(all_updates):
    if not os.path.exists(CSV_FILE):
        log(f"Error: {CSV_FILE} not found.")
        return False

    df = pd.read_csv(CSV_FILE)
    for profile_name, usage_grams in all_updates:
        mask = df['Profile Name'] == profile_name
        if mask.any():
            current_weight = df.loc[mask, 'Weight (g)'].iloc[0]
            new_weight = round(float(current_weight) - usage_grams, 2)
            df.loc[mask, 'Weight (g)'] = new_weight
            log(f"   >>> Deducted {usage_grams}g from '{profile_name}'. New Stock: {new_weight}g")
        else:
            log(f"   !!! NOT FOUND: '{profile_name}' not in CSV.")

    df.to_csv(CSV_FILE, index=False)
    generate_html(df)
    return True

def generate_html(df):
    df_sorted = df.sort_values(by='Weight (g)', ascending=True)
    html_table = df_sorted.to_html(classes='inventory-table', index=False)
    
    html_content = f"""
    <html>
    <head>
        <title>Filament Inventory</title>
        <style>
            body {{ font-family: sans-serif; margin: 40px; background: #f4f4f4; }}
            .inventory-table {{ border-collapse: collapse; width: 100%; background: white; }}
            .inventory-table th, .inventory-table td {{ border: 1px solid #ddd; padding: 12px; }}
            .inventory-table th {{ background-color: #24292e; color: white; }}
            .low-stock {{ color: red; font-weight: bold; }}
        </style>
    </head>
    <body>
        <h1>Filament Inventory Dashboard</h1>
        {html_table}
        <p>Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </body>
    </html>
    """
    with open(HTML_FILE, 'w') as f:
        f.write(html_content)

def main():
    if not os.path.exists(INPUT_FOLDER): os.makedirs(INPUT_FOLDER)
    files = [f for f in os.listdir(INPUT_FOLDER) if f.lower().endswith('.gcode')]
    if not files:
        if os.path.exists(CSV_FILE): generate_html(pd.read_csv(CSV_FILE))
        return

    all_updates = []
    processed_files = []
    for filename in files:
        updates = get_filament_data(os.path.join(INPUT_FOLDER, filename))
        if updates:
            all_updates.extend(updates)
            processed_files.append(filename)

    if all_updates and update_csv_and_generate_html(all_updates):
        if not os.path.exists(ARCHIVE_FOLDER): os.makedirs(ARCHIVE_FOLDER)
        for f in processed_files:
            shutil.move(os.path.join(INPUT_FOLDER, f), os.path.join(ARCHIVE_FOLDER, f))

if __name__ == "__main__":
    main()
