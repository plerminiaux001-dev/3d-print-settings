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

def generate_combined_html(df):
    # Sort inventory by weight (lowest first)
    df_sorted = df.sort_values(by='Weight (g)', ascending=True)
    
    # Logic to color-code the Weight column based on stock
    def get_stock_style(weight):
        if weight <= 0: return "color: #d9534f; font-weight: bold;" # Red-ish
        if weight < 250: return "color: #f0ad4e; font-weight: bold;" # Orange-ish
        return "color: #6b8e23;" # Sage Green

    inventory_rows = ""
    for _, row in df_sorted.iterrows():
        style = get_stock_style(row['Weight (g)'])
        inventory_rows += f"""
            <tr>
                <td>{row['Filament Name']}</td>
                <td>{row['Color']}</td>
                <td style="{style}">{row['Weight (g)']}g</td>
                <td>{row['Profile Name']}</td>
                <td>{row['Type']}</td>
            </tr>"""

    full_html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>3D Printing Hub: Settings & Inventory</title>
    <style>
        :root {{
            --primary-earth: #6b8e23; /* Olive Drab */
            --secondary-earth: #8b4513; /* Saddle Brown */
            --bg-color: #fdfaf5; /* Cream White */
            --text-color: #3e3e3e;
            --border-color: #d2c4b5;
            --header-bg: #4a5d4e; /* Dark Slate Green */
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            line-height: 1.6;
            color: var(--text-color);
            margin: 0;
            background-color: var(--bg-color);
        }}

        .container {{ max-width: 900px; margin: 0 auto; padding: 2rem; background: white; box-shadow: 0 0 20px rgba(0,0,0,0.05); }}

        header {{
            background: var(--header-bg);
            color: white;
            padding: 2rem;
            text-align: center;
            border-radius: 8px 8px 0 0;
            margin: -2rem -2rem 2rem -2rem;
        }}

        h1, h2, h3 {{ color: var(--secondary-earth); border-bottom: 1px solid var(--border-color); padding-bottom: 0.3rem; }}
        h1 {{ border: none; margin: 0; color: white; }}

        /* Inventory Table Styling */
        .inventory-section {{ margin-bottom: 4rem; padding: 1rem; border: 2px solid var(--primary-earth); border-radius: 8px; }}
        table {{ width: 100%; border-collapse: collapse; margin: 1rem 0; font-size: 0.9rem; }}
        th {{ background-color: var(--primary-earth); color: white; text-align: left; padding: 12px; }}
        td {{ border-bottom: 1px solid var(--border-color); padding: 10px; }}
        tr:hover {{ background-color: #f1f8e9; }}

        .step-box {{ background-color: #f9f6f2; border-left: 5px solid var(--secondary-earth); padding: 1rem; margin: 1rem 0; }}
        code {{ background: #e8e0d5; padding: 0.2rem 0.4rem; border-radius: 4px; font-size: 90%; }}
        footer {{ text-align: center; margin-top: 3rem; color: #888; font-size: 0.8rem; border-top: 1px solid var(--border-color); padding-top: 1rem; }}
    </style>
</head>
<body>
<div class="container">
    <header>
        <h1>3D Printing Hub</h1>
        <p>Filament Inventory & Technical Guides</p>
    </header>

    <main>
        <section class="inventory-section">
            <h2>Current Filament Stock</h2>
            <table>
                <thead>
                    <tr>
                        <th>Filament</th>
                        <th>Color</th>
                        <th>Weight</th>
                        <th>Slicer Profile</th>
                        <th>Type</th>
                    </tr>
                </thead>
                <tbody>
                    {inventory_rows}
                </tbody>
            </table>
            <p style="font-size: 0.8rem; font-style: italic;">Auto-updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
        </section>

        <section id="fusion-solutions">
            <h2>1. Solutions in Fusion 360</h2>
            <h3>Method A: Offset Face (The Correct Way)</h3>
            <p>Instead of Press/Pull, use the specific Offset Face command.</p>
            <div class="step-box">
                <ol>
                    <li>Go to <strong>Solid Tab > Modify > Offset Face</strong>.</li>
                    <li>Select the <strong>angled faces</strong> (flanks) of the thread.</li>
                    <li>Enter your offset value (Standard: <code>-0.15mm</code>).</li>
                </ol>
            </div>
        </section>

        <section id="tolerances">
            <h2>2. Slicer Compensations</h2>
            <p>Use <strong>X-Y Hole Compensation</strong> for internal threads if CAD is unavailable.</p>
        </section>
    </main>

    <footer>
        <p>Built with Python & GitHub Actions | Keep Printing.</p>
    </footer>
</div>
</body>
</html>
"""
    with open(HTML_FILE, "w", encoding='utf-8') as f:
        f.write(full_html)

# ... (Rest of your processing logic from the previous update_inventory.py script)
