import streamlit as st
import pandas as pd
import re
import io

def parse_data(raw_text):
    # Regex pattern to find the start of a record (Cons. ID)
    # Looks for 'DD' followed by 6 digits and alphanumeric chars
    record_start_pattern = re.compile(r'(DD\d{6}[A-Z0-9]+)')
    
    # Split the text by the Cons. ID, keeping the delimiter
    parts = record_start_pattern.split(raw_text)
    
    # The first element is usually empty or header text before the first ID
    # We process pairs: (Cons_ID, Content_Body)
    records = []
    
    # Iterate through the split parts
    # parts[0] is trash, parts[1] is ID, parts[2] is body, parts[3] is ID, etc.
    for i in range(1, len(parts), 2):
        if i+1 < len(parts):
            cons_id = parts[i].strip()
            body = parts[i+1].strip()
            
            record = extract_fields(cons_id, body)
            records.append(record)
            
    return pd.DataFrame(records)

def extract_fields(cons_id, text_block):
    # 1. Order ID (6 digits)
    order_id_match = re.search(r'\b(\d{6})\b', text_block)
    order_id = order_id_match.group(1) if order_id_match else ""

    # 2. Store Name (Match known patterns or fallback)
    # Matching specific store names found in your data
    store_match = re.search(r'(Deen Commerce|w DEEN WARI OUTLET|c DEEN CUMILLA OUTLET)', text_block)
    store = store_match.group(1) if store_match else ""

    # 3. Phone Number (01 followed by 9 digits)
    phone_match = re.search(r'(01\d{9})', text_block)
    phone = phone_match.group(1) if phone_match else ""

    # 4. Amounts (COD, Charge, Discount)
    cod_match = re.search(r'COD\s*৳?\s*([\d,]+)', text_block)
    cod = cod_match.group(1).replace(',', '') if cod_match else "0"
    
    charge_match = re.search(r'Charge\s*৳?\s*([\d,.]+)', text_block)
    charge = charge_match.group(1).replace(',', '') if charge_match else "0"
    
    discount_match = re.search(r'Discount\s*৳?\s*([\d,]+)', text_block)
    discount = discount_match.group(1).replace(',', '') if discount_match else "0"

    # 5. Payment Status
    status = "Unpaid"
    if "Paid" in text_block and "Unpaid" not in text_block:
        status = "Paid"
    
    # 6. Payment Date
    paid_date_match = re.search(r'Paid At:\s*([\d/]+)', text_block)
    paid_date = paid_date_match.group(1) if paid_date_match else ""

    # 7. Delivery Status
    # Look for 'Updated on...' and capture the context before it
    delivery_match = re.search(r'(At Delivery Hub|Paid Return|Urgent Delivery Requested|Returned)', text_block)
    delivery_status = delivery_match.group(1) if delivery_match else ""
    
    updated_match = re.search(r'Updated on\s*([\d/]+)', text_block)
    if updated_match:
        delivery_status += f" Updated on {updated_match.group(1)}"

    # 8. Recipient Name & Address Logic
    # Strategy: Remove known metadata to isolate name and address
    # Remove lines containing specific keywords
    lines = text_block.split('\n')
    info_lines = []
    ignore_keywords = ['Type:', 'Parcel', 'COD', 'Charge', 'Discount', 'Paid', 'Unpaid', 
                       'View POD', 'Action', 'Updated on', 'Paid At:', store, order_id, cons_id]
    
    for line in lines:
        clean_line = line.strip()
        if not clean_line: continue
        
        # Skip phone numbers
        if re.match(r'01\d{9}', clean_line): continue
        
        # Skip lines with ignore keywords
        should_ignore = False
        for kw in ignore_keywords:
            if kw.lower() in clean_line.lower():
                should_ignore = True
                break
        
        if not should_ignore:
            info_lines.append(clean_line)

    # Heuristic for Name vs Address
    # Usually Name is the first line, Address is the rest.
    # But we need to filter out the Order ID line if it survived (it usually does)
    
    filtered_info = []
    for line in info_lines:
        # Filter out lines that are purely numeric or very short garbage
        if line.isdigit(): continue
        filtered_info.append(line)

    name = ""
    address = ""
    
    if len(filtered_info) > 0:
        name = filtered_info[0]
    if len(filtered_info) > 1:
        address = ", ".join(filtered_info[1:])

    return {
        "Cons. ID": cons_id,
        "Order ID": order_id,
        "Store": store,
        "Recipient Name": name,
        "Address": address,
        "Phone": phone,
        "Delivery Status": delivery_status,
        "COD Amount": cod,
        "Charge": charge,
        "Discount": discount,
        "Payment Status": status,
        "Payment Date": paid_date
    }

# --- Streamlit UI ---

st.set_page_config(page_title="Order Data Converter", layout="wide")

st.title("📦 Order Data to Spreadsheet Converter")
st.markdown("""
Paste your raw order text data below. The app will automatically format it into a table.
**Instructions:**
1. Copy the text from your source.
2. Paste it into the text area below.
3. Click 'Process Data'.
4. Download the result as CSV or Excel.
""")

input_text = st.text_area("Raw Data Input", height=300, placeholder="Paste your data here starting with Cons. ID...")

if st.button("Process Data", type="primary"):
    if input_text.strip() == "":
        st.warning("Please paste some data first.")
    else:
        with st.spinner('Processing...'):
            df = parse_data(input_text)
            
            if df.empty:
                st.error("No valid records found. Please check the data format.")
            else:
                st.success(f"Found {len(df)} records!")
                st.dataframe(df, use_container_width=True)
                
                # CSV Download
                csv = df.to_csv(index=False).encode('utf-8-sig')
                st.download_button(
                    label="📥 Download CSV",
                    data=csv,
                    file_name='processed_orders.csv',
                    mime='text/csv',
                )
                
                # Excel Download (Using BytesIO)
                buffer = io.BytesIO()
                with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                    df.to_excel(writer, index=False, sheet_name='Orders')
                st.download_button(
                    label="📥 Download Excel",
                    data=buffer,
                    file_name="processed_orders.xlsx",
                    mime="application/vnd.ms-excel"
                )