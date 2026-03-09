import re
from io import BytesIO
from datetime import datetime

import pandas as pd
import streamlit as st

st.set_page_config(page_title="Delivery Text to Spreadsheet", layout="wide")
st.title("Delivery Text to Spreadsheet")
st.caption("Paste raw delivery text, parse it, then download as Excel.")

HEADER_TOKENS = {
    "Cons. ID",
    "Order ID",
    "Store",
    "Recipient Info",
    "Delivery Status",
    "Amount",
    "Payment",
    "Action",
}


def clean_lines(raw: str):
    lines = []
    for line in raw.splitlines():
        value = line.strip()
        if not value:
            continue
        if value in HEADER_TOKENS:
            continue
        lines.append(value)
    return lines


def is_consignment_id(value: str) -> bool:
    return bool(re.match(r"^[A-Z]{2}\d{6}[A-Z0-9]+$", value))


def parse_amount(line: str):
    m = re.search(r"([\d,]+(?:\.\d+)?)", line)
    if not m:
        return 0.0
    return float(m.group(1).replace(",", ""))


def parse_date(line: str):
    if line.lower().startswith("updated on"):
        return line.split("Updated on", 1)[1].strip()
    return line.strip()


def parse_records(raw: str):
    lines = clean_lines(raw)
    records = []
    i = 0

    while i < len(lines):
        if not is_consignment_id(lines[i]):
            i += 1
            continue

        rec = {
            "Consignment ID": lines[i],
            "Type": "",
            "Order ID": "",
            "Store": "",
            "Recipient Name": "",
            "Address": "",
            "Phone": "",
            "Delivery Status": "",
            "Status Updated On": "",
            "COD Amount": 0.0,
            "Charge": 0.0,
            "Discount": 0.0,
            "Payment Status": "",
            "Action": "",
        }
        i += 1

        if i < len(lines) and lines[i].startswith("Type"):
            i += 1
        if i < len(lines):
            rec["Type"] = lines[i]
            i += 1

        if i < len(lines):
            rec["Order ID"] = lines[i]
            i += 1
        if i < len(lines):
            rec["Store"] = lines[i]
            i += 1
        if i < len(lines):
            rec["Recipient Name"] = lines[i]
            i += 1
        if i < len(lines):
            rec["Address"] = lines[i]
            i += 1
        if i < len(lines):
            rec["Phone"] = lines[i]
            i += 1

        status_lines = []
        while i < len(lines) and not lines[i].startswith("Updated on"):
            status_lines.append(lines[i])
            i += 1
        rec["Delivery Status"] = "; ".join(status_lines)

        if i < len(lines) and lines[i].startswith("Updated on"):
            rec["Status Updated On"] = parse_date(lines[i])
            i += 1

        if i < len(lines):
            rec["COD Amount"] = parse_amount(lines[i])
            i += 1
        if i < len(lines):
            rec["Charge"] = parse_amount(lines[i])
            i += 1
        if i < len(lines):
            rec["Discount"] = parse_amount(lines[i])
            i += 1

        if i < len(lines):
            rec["Payment Status"] = lines[i]
            i += 1

        action_lines = []
        while i < len(lines) and not is_consignment_id(lines[i]):
            if not lines[i].startswith("Type"):
                action_lines.append(lines[i])
            i += 1
        rec["Action"] = ", ".join(action_lines)

        records.append(rec)

    return pd.DataFrame(records)


def extract_fields_fuzzy(cons_id, text_block):
    order_id_match = re.search(r'\b(\d{6})\b', text_block)
    order_id = order_id_match.group(1) if order_id_match else ""

    store_match = re.search(r'(Deen Commerce|w DEEN WARI OUTLET|c DEEN CUMILLA OUTLET)', text_block)
    store = store_match.group(1) if store_match else ""

    phone_match = re.search(r'(01\d{9})', text_block)
    phone = phone_match.group(1) if phone_match else ""

    cod_match = re.search(r'COD\s*৳?\s*([\d,]+)', text_block)
    cod = cod_match.group(1).replace(',', '') if cod_match else "0"
    
    charge_match = re.search(r'Charge\s*৳?\s*([\d,.]+)', text_block)
    charge = charge_match.group(1).replace(',', '') if charge_match else "0"
    
    discount_match = re.search(r'Discount\s*৳?\s*([\d,]+)', text_block)
    discount = discount_match.group(1).replace(',', '') if discount_match else "0"

    status = "Unpaid"
    if "Paid" in text_block and "Unpaid" not in text_block:
        status = "Paid"
    
    delivery_match = re.search(r'(At Delivery Hub|Paid Return|Urgent Delivery Requested|Returned)', text_block)
    delivery_status = delivery_match.group(1) if delivery_match else ""
    
    updated_match = re.search(r'Updated on\s*([\d/]+)', text_block)
    status_updated_on = updated_match.group(1) if updated_match else ""

    lines = text_block.split('\n')
    info_lines = []
    ignore_keywords = ['Type:', 'Parcel', 'COD', 'Charge', 'Discount', 'Paid', 'Unpaid', 
                       'View POD', 'Action', 'Updated on', 'Paid At:', store, order_id, cons_id]
    
    for line in lines:
        clean_line = line.strip()
        if not clean_line: continue
        if re.match(r'01\d{9}', clean_line): continue
        
        should_ignore = False
        for kw in ignore_keywords:
            if kw and kw.lower() in clean_line.lower():
                should_ignore = True
                break
        
        if not should_ignore:
            info_lines.append(clean_line)

    filtered_info = []
    for line in info_lines:
        if line.isdigit(): continue
        filtered_info.append(line)

    name = ""
    address = ""
    
    if len(filtered_info) > 0:
        name = filtered_info[0]
    if len(filtered_info) > 1:
        address = ", ".join(filtered_info[1:])

    return {
        "Consignment ID": cons_id,
        "Type": "",
        "Order ID": order_id,
        "Store": store,
        "Recipient Name": name,
        "Address": address,
        "Phone": phone,
        "Delivery Status": delivery_status,
        "Status Updated On": status_updated_on,
        "COD Amount": float(cod) if cod else 0.0,
        "Charge": float(charge) if charge else 0.0,
        "Discount": float(discount) if discount else 0.0,
        "Payment Status": status,
        "Action": ""
    }

def parse_data_fuzzy(raw_text):
    record_start_pattern = re.compile(r'(DD\d{6}[A-Z0-9]+)')
    parts = record_start_pattern.split(raw_text)
    records = []
    for i in range(1, len(parts), 2):
        if i+1 < len(parts):
            cons_id = parts[i].strip()
            body = parts[i+1].strip()
            record = extract_fields_fuzzy(cons_id, body)
            records.append(record)
    return pd.DataFrame(records)


def df_to_excel_bytes(df: pd.DataFrame) -> bytes:
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Deliveries")
        ws = writer.book["Deliveries"]
        ws.freeze_panes = "A2"

        widths = {
            "A": 18,
            "B": 10,
            "C": 12,
            "D": 18,
            "E": 20,
            "F": 60,
            "G": 14,
            "H": 30,
            "I": 16,
            "J": 12,
            "K": 10,
            "L": 10,
            "M": 14,
            "N": 14,
        }
        for col, width in widths.items():
            ws.column_dimensions[col].width = width

        for row in range(2, ws.max_row + 1):
            ws[f"J{row}"].number_format = "#,##0.00"
            ws[f"K{row}"].number_format = "#,##0.00"
            ws[f"L{row}"].number_format = "#,##0.00"

    output.seek(0)
    return output.read()


sample = """Cons. ID
DD040326KR9NUU
Type:
Parcel
193252
Deen Commerce
Raafin
House 10, Road 15, Sector 11, Uttara West, Dhaka
01745166722
At Delivery Hub
Updated on 05/03/2026
COD ৳ 0
Charge ৳ 50
Discount ৳ 10
Unpaid
View
POD"""

tab1, tab2 = st.tabs(["Standard Parser", "Fuzzy Text Parser"])

with tab1:
    st.markdown("### Strict Text Parser")
    raw_text = st.text_area(
        "Paste raw text",
        value=sample,
        height=360,
        placeholder="Paste the full block copied from your courier page...",
        key="standard_raw_text"
    )

    col1, col2 = st.columns([1, 1])
    with col1:
        parse_clicked = st.button("Parse Data", type="primary", key="standard_btn")
    with col2:
        filename = st.text_input(
            "Output filename",
            value=f"deliveries_{datetime.now().strftime('%d-%m-%Y')}.xlsx",
            key="standard_filename"
        )

    if parse_clicked:
        df = parse_records(raw_text)
        if df.empty:
            st.error("No records found. Please check the pasted text format.")
        else:
            st.success(f"Parsed {len(df)} record(s).")
            st.dataframe(df, use_container_width=True)

            xlsx_bytes = df_to_excel_bytes(df)

            st.download_button(
                label="Download XLSX",
                data=xlsx_bytes,
                file_name=filename,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key="standard_dl"
            )

            save_to_downloads = st.button("Save to Downloads on this PC", key="standard_save")
            if save_to_downloads:
                import os
                downloads = os.path.join(os.path.expanduser("~"), "Downloads")
                out_path = os.path.join(downloads, filename)
                with open(out_path, "wb") as f:
                    f.write(xlsx_bytes)
                st.info(f"Saved: {out_path}")

with tab2:
    st.markdown("### Fuzzy Text to Spreadsheet")
    st.info("Converts unstructured or fuzzy text into a spreadsheet. First tries strict parsing, then falls back to fuzzy regex matching.")
    
    fuzzy_raw_text = st.text_area(
        "Paste fuzzy text",
        value="",
        height=360,
        placeholder="Paste your data here...",
        key="fuzzy_raw_text"
    )
    
    col3, col4 = st.columns([1, 1])
    with col3:
        fuzzy_parse_clicked = st.button("Process Fuzzy Data", type="primary", key="fuzzy_btn")
    with col4:
        fuzzy_filename = st.text_input(
            "Output filename",
            value=f"fuzzy_deliveries_{datetime.now().strftime('%d-%m-%Y')}.xlsx",
            key="fuzzy_filename"
        )

    if fuzzy_parse_clicked:
        if fuzzy_raw_text.strip() == "":
            st.warning("Please paste some data first.")
        else:
            with st.spinner('Processing data...'):
                try:
                    df_fuzzy = parse_records(fuzzy_raw_text)
                except Exception:
                    df_fuzzy = pd.DataFrame()

                if df_fuzzy.empty:
                    st.info("Strict parser yielded no results. Using fuzzy regex parser...")
                    try:
                        df_fuzzy = parse_data_fuzzy(fuzzy_raw_text)
                    except Exception:
                        df_fuzzy = pd.DataFrame()

                if df_fuzzy.empty:
                    st.error("No valid records found using either parser. Please check your data format.")
                else:
                    st.success(f"Successfully processed {len(df_fuzzy)} record(s).")
                    st.dataframe(df_fuzzy, use_container_width=True)

                    xlsx_bytes_fuzzy = df_to_excel_bytes(df_fuzzy)

                    st.download_button(
                        label="Download XLSX",
                        data=xlsx_bytes_fuzzy,
                        file_name=fuzzy_filename,
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        key="fuzzy_dl"
                    )

                    save_to_downloads_fuzzy = st.button("Save to Downloads on this PC", key="fuzzy_save")
                    if save_to_downloads_fuzzy:
                        import os
                        downloads = os.path.join(os.path.expanduser("~"), "Downloads")
                        out_path = os.path.join(downloads, fuzzy_filename)
                        with open(out_path, "wb") as f:
                            f.write(xlsx_bytes_fuzzy)
                        st.info(f"Saved: {out_path}")

st.markdown("Run with: `streamlit run app.py`")

