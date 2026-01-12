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

def generate_html(df):
    # 1. Sort by weight and build table
    df_sorted = df.sort_values('Weight (g)')
    rows = ""
    for _, row in df_sorted.iterrows():
        color = "#d9534f" if row['Weight (g)'] < 250 else "#6b8e23"
        rows += f"<tr><td>{row['Filament Name']}</td><td>{row['Color']}</td><td style='color:{color}; font-weight:bold;'>{row['Weight (g)']}g</td><td>{row['Profile Name']}</td></tr>"
    
    table_html = f"<table><thead><tr><th>Filament</th><th>Color</th><th>Stock</th><th>Profile</th></tr></thead><tbody>{rows}</tbody></table>"

    # 2. Read Template and Inject
    if not os.path.exists(TEMPLATE_FILE):
        print("Template.html not found!")
        return

    with open(TEMPLATE_FILE, 'r', encoding='utf-8') as f:
        content = f.read()

    content = content.replace('', table_html)
    content = content.replace('', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

    # 3. Create fresh index.html
    with open(HTML_FILE, 'w', encoding='utf-8') as f:
        f.write(content)

def main():
    if not os.path.exists(INPUT_FOLDER): os.makedirs(INPUT_FOLDER)
    files = [f for f in os.listdir(INPUT_FOLDER) if f.lower().endswith('.gcode')]
    df = pd.read_csv(CSV_FILE)
    
    if files:
        for filename in files:
            path = os.path.join(INPUT_FOLDER, filename)
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                c = f.read()
                w_match = re.search(r"; filament used \[g\] = (.+)", c)
                n_match = re.search(r'; filament_settings_id = (.+)', c)
                if w_match and n_match:
                    usage = float(w_match.group(1).split(',')[0])
                    name = n_match.group(1).replace('"', '').strip()
                    mask = df['Profile Name'] == name
                    if mask.any():
                        df.loc[mask, 'Weight (g)'] = round(df.loc[mask, 'Weight (g)'].iloc[0] - usage, 2)
            
            if not os.path.exists(ARCHIVE_FOLDER): os.makedirs(ARCHIVE_FOLDER)
            shutil.move(path, os.path.join(ARCHIVE_FOLDER, filename))
        
        df.to_csv(CSV_FILE, index=False)
    
    generate_html(df)

if __name__ == "__main__":
    main()
