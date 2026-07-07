import json
import re
import os
from typing import Dict, Any

def extract_invoice_details(file_path: str) -> str:
    """
    Reads a text-based invoice file and extracts 'Total Amount', 'Vendor Name', 
    and 'Date' into a JSON-formatted string.

    Args:
        file_path (str): The absolute or relative path to the text-based invoice file.

    Returns:
        str: A JSON-formatted string containing the extracted fields:
             - "Vendor Name" (str or null)
             - "Date" (str or null)
             - "Total Amount" (float or null)
             If the file doesn't exist or cannot be read, returns JSON with an "error" key.
    """
    if not os.path.exists(file_path):
        return json.dumps({
            "error": f"File not found: {file_path}",
            "Vendor Name": None,
            "Date": None,
            "Total Amount": None
        }, indent=4)

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        return json.dumps({
            "error": f"Failed to read file: {str(e)}",
            "Vendor Name": None,
            "Date": None,
            "Total Amount": None
        }, indent=4)

    # --- 1. Extract Date ---
    # Common date formats (e.g., YYYY-MM-DD, DD/MM/YYYY, July 7, 2026)
    date_patterns = [
        # YYYY-MM-DD or YYYY/MM/DD
        r'\b\d{4}[-/.]\d{2}[-/.]\d{2}\b',
        # DD-MM-YYYY or DD/MM/YYYY or MM/DD/YYYY
        r'\b\d{1,2}[-/.]\d{1,2}[-/.]\d{4}\b',
        # Month Day, Year (e.g., July 7, 2026 or Jul 7, 2026)
        r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2},? \d{4}\b',
        # Day Month Year (e.g., 7 July 2026 or 7 Jul 2026)
        r'\b\d{1,2} (?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{4}\b'
    ]
    
    extracted_date = None
    
    # Check lines with common date prefixes first
    date_label_match = re.search(r'(?:date|invoice\s+date|issued\s+on|billing\s+date)\s*[:\-]?\s*(.*)', content, re.IGNORECASE)
    if date_label_match:
        potential_date_str = date_label_match.group(1).strip()
        for pattern in date_patterns:
            m = re.search(pattern, potential_date_str, re.IGNORECASE)
            if m:
                extracted_date = m.group(0)
                break
                
    # Fallback to search the entire document
    if not extracted_date:
        for pattern in date_patterns:
            m = re.search(pattern, content, re.IGNORECASE)
            if m:
                extracted_date = m.group(0)
                break

    # --- 2. Extract Total Amount ---
    # Match total amounts, checking for common labels first.
    amount_patterns = [
        # Match "Total", "Total Amount", "Amount Due", "Grand Total", etc.
        r'(?:total|amount\s+due|total\s+due|grand\s+total|balance\s+due|net\s+total|invoice\s+total)\s*[:\-]?\s*(?:\$|usd|eur|gbp|€|£)?\s*([\d,]+\.\d{2})\b',
        # Near word "total" or "due" find any currency amount
        r'(?:total|due|payable|amount)[\s\S]{0,50}?(?:\$|usd|eur|gbp|€|£)\s*([\d,]+\.\d{2})\b'
    ]
    
    extracted_amount = None
    for pattern in amount_patterns:
        m = re.search(pattern, content, re.IGNORECASE)
        if m:
            extracted_amount = m.group(1).replace(',', '')
            break
            
    # Fallback to any pattern matching a decimal currency-like figure
    if not extracted_amount:
        m = re.search(r'(?:\$|usd|eur|gbp|€|£)\s*([\d,]+\.\d{2})\b', content, re.IGNORECASE)
        if m:
            extracted_amount = m.group(1).replace(',', '')

    # --- 3. Extract Vendor Name ---
    # Vendor names are usually highlighted by prefixes or are at the top of the invoice.
    vendor_patterns = [
        r'(?:vendor|seller|merchant|billed\s+by|from|issuer|company|service\s+provider)\s*[:\-]\s*(.*)'
    ]
    
    extracted_vendor = None
    for pattern in vendor_patterns:
        m = re.search(pattern, content, re.IGNORECASE)
        if m:
            raw_vendor = m.group(1).strip()
            
            # Clean up for single-line structures: split by sentence period boundaries or newlines
            parts = re.split(r'\.\s+|\n', raw_vendor)
            if parts:
                extracted_vendor = parts[0].strip()
            else:
                extracted_vendor = raw_vendor
                
            # If the name still contains key label indicator words, truncate there
            label_indicators = [r'\bdate\b', r'\btotal\b', r'\bamount\b', r'\bitems\b', r'\binvoice\b']
            for indicator in label_indicators:
                extracted_vendor = re.split(indicator, extracted_vendor, flags=re.IGNORECASE)[0].strip()
            
            # Clean trailing punctuation
            extracted_vendor = extracted_vendor.rstrip('.,;:-')
            break
            
    if not extracted_vendor:
        # Fallback: scan lines from the top, picking the first non-empty line
        # that doesn't contain generic words like "invoice" or "bill".
        lines = [line.strip() for line in content.split('\n') if line.strip()]
        skip_keywords = {'invoice', 'bill', 'receipt', 'statement', 'tax invoice', 'purchase order', 'po', 'to:', 'client:'}
        for line in lines[:5]:
            if not any(kw in line.lower() for kw in skip_keywords):
                extracted_vendor = line
                break

    # Construct the resulting data dict
    result = {
        "Vendor Name": extracted_vendor,
        "Date": extracted_date,
        "Total Amount": float(extracted_amount) if extracted_amount else None
    }
    
    return json.dumps(result, indent=4)

def process_all_invoices(directory_path: str) -> str:
    """
    Loops through all .txt files in the given directory, extracts invoice details 
    from each, consolidates the results into a single list (flagging invoices 
    exceeding $500 as 'High Priority'), and saves the report as 'summary_report.json' 
    in the target directory.

    Args:
        directory_path (str): The path to the directory containing .txt invoices.

    Returns:
        str: A JSON-formatted string of the consolidated summary report.
    """
    if not os.path.exists(directory_path) or not os.path.isdir(directory_path):
        return json.dumps({
            "error": f"Invalid directory path: {directory_path}",
            "invoices": []
        }, indent=4)

    consolidated_results = []
    
    try:
        filenames = sorted(os.listdir(directory_path))
    except Exception as e:
        return json.dumps({
            "error": f"Failed to list directory: {str(e)}",
            "invoices": []
        }, indent=4)

    for filename in filenames:
        if filename.endswith(".txt") and filename != "summary_report.json":
            file_path = os.path.join(directory_path, filename)
            
            # Extract details using existing function
            details_json_str = extract_invoice_details(file_path)
            details = json.loads(details_json_str)
            
            if "error" in details:
                entry = {
                    "File Name": filename,
                    "Vendor Name": None,
                    "Date": None,
                    "Total Amount": None,
                    "Priority": "Error",
                    "Error": details["error"]
                }
            else:
                total_amount = details.get("Total Amount")
                priority = "Normal"
                if total_amount is not None and total_amount > 500.0:
                    priority = "High Priority"
                
                entry = {
                    "File Name": filename,
                    "Vendor Name": details.get("Vendor Name"),
                    "Date": details.get("Date"),
                    "Total Amount": total_amount,
                    "Priority": priority
                }
                
            consolidated_results.append(entry)
            
    report = {
        "invoices": consolidated_results
    }
    
    report_path = os.path.join(directory_path, "summary_report.json")
    try:
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=4)
    except Exception as e:
        report["error_saving_report"] = f"Failed to save summary_report.json: {str(e)}"
        
    return json.dumps(report, indent=4)
