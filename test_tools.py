import tools
import json

def main():
    print("--- Testing Individual Invoice Extraction ---")
    result_json = tools.extract_invoice_details("Sample-data/invoice01.txt")
    print(result_json)
    
    print("\n--- Testing Batch Invoice Processing ---")
    consolidated_json = tools.process_all_invoices("Sample-data")
    print("Consolidated Summary Report:")
    print(consolidated_json)

if __name__ == "__main__":
    main()
