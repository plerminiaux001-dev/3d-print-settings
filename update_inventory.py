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
    def get_color(w):
        if w <= 0: return "#d9534f" # Red
        if w < 250: return "#f0ad4e" # Orange
        return "#6b8e23" # Earth Green

    inventory_rows = ""
    for _, row in df.sort_values('Weight (g)').iterrows():
        color = get_color(row['Weight (g)'])
        inventory_rows += f"""
        <tr>
            <td>{row['Filament Name']}</td>
            <td>{row['Color']}</td>
            <td style="color: {color}; font-weight: bold;">{row['Weight (g)']}g</td>
            <td style="font-size: 0.8rem; color: #666;">{row['Profile Name']}</td>
        </tr>"""

    html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>3D Printing Hub</title>
    <style>
        :root {{ --earth-green: #6b8e23; --earth-brown: #8b4513; --cream: #fdfaf5; --text: #3e3e3e; }}
        body {{ font-family: -apple-system, sans-serif; background: var(--cream); color: var(--text); line-height: 1.6; margin: 0; }}
        .container {{ max-width: 850px; margin: 2rem auto; background: white; padding: 2rem; box-shadow: 0 10px 30px rgba(0,0,0,0.05); border-radius: 8px; }}
        header {{ background: #4a5d4e; color: white; padding: 1.5rem; margin: -2rem -2rem 2rem -2rem; border-radius: 8px 8px 0 0; text-align: center; }}
        h2 {{ border-bottom: 2px solid #d2c4b5; padding-bottom: 5px; color: var(--earth-brown); }}
        table {{ width: 100%; border-collapse: collapse; margin-bottom: 3rem; }}
        th {{ background: var(--earth-green); color: white; text-align: left; padding: 12px; }}
        td {{ padding: 10px; border-bottom: 1px solid #eee; }}
        .step-box {{ background: #f9f6f2; border-left: 5px solid var(--earth-brown); padding: 1rem; margin: 1rem 0; }}
    </style>
</head>
<body>
<div class="container">
    <header><h1>3D Printing Hub</h1><p>Inventory & Reference Guide</p></header>
    <section>
        <h2>Filament Inventory</h2>
        <table>
            <thead><tr><th>Filament</th><th>Color</th><th>Stock</th><th>Slicer Profile</th></tr></thead>
            <tbody>{inventory_rows}</tbody>
        </table>
    </section>
    <section>
        <h2>Fusion 360 Guide</h2>
        <div class="step-box">
            <p>Use <b>Modify > Offset Face</b> with <code>-0.15mm</code> for standard threads.</p>
        </div>
    </section>
    <footer><p>Sync Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p></footer>
</div>
</body>
</html>
"""
    with open(HTML_FILE, 'w', encoding='utf-8') as f:
        f.write(html_content)

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
