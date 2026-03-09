import json

with open(r'h:\Analysis\New_\Fuzzy Data to SpreadSheet\app_gpt.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

out_lines = []
in_main = False
for line in lines:
    if line.startswith('st.set_page_config'):
        continue
    if line.startswith('st.title'):
        continue
    if line.startswith('st.caption'):
        continue
    if line.startswith('st.markdown("Run with:'):
        continue
    if line.startswith('sample = """'):
        in_main = True
        out_lines.append('def render_fuzzy_parser_tab():\n')
        out_lines.append('    st.markdown("### 📄 Delivery Text to Spreadsheet")\n')
        out_lines.append('    st.caption("Paste raw delivery text, parse it, then download as Excel.")\n')
    
    if in_main:
        out_lines.append('    ' + line if line.strip() else '\n')
    else:
        out_lines.append(line)

with open(r'h:\Analysis\New_\app_modules\fuzzy_parser_tab.py', 'w', encoding='utf-8') as f:
    f.writelines(out_lines)

print("Done")
