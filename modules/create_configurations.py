import json
import os

def create_json_file():
    """
    Creates a JSON file with the provided values.

    Args:
        file_path (str): Path to save the JSON file.
        values (dict): Dictionary containing key-value pairs for the JSON file.

    Returns:
        None
    """
    file_path = r"C:\barcode\barcode.json"
    values = {
        "server": "192.168.1.22\A2006",
        "database": "AED_ALPHA_FE",
        "username": "test",
        "password": "test",
        "vid": "0x1234",
        "pid": "0x5678",
        "endpoint": "0x01",
        "companyName": "Example Corp",
        "location": "HQ",
        "useZPL": True,
        "ip_address": "192.168.1.100",
        "wireless_mode": False,
        "zplTemplate": "^XA \n^LH0,-7\n^C128\n^PR3\n^PW280 \n^FO10,0,^A0N,20,20^FD{{companyName}}^FS ^FO10,25^A0N,15,20^FD{{barcode_value}}^FS ^FO10,40^BY1,1.5,0^BCN,50,N,Y,N,N^FD{{barcode_value}}^FS \n^A0N,50,50\n^FO10,94^A0N,15,20^FB280,3,0,L,0 ^FD{{description}}^FS ^FO10,130^A0N,25,30^FD{{unit_price_integer}}^FS \n^PQ{{copies}} \n^XZ",
        "tpslTemplate": "SPEED 2.0 \nDENSITY 7 \nDIRECTION 0 \nSIZE 35MM,25MM \nOFFSET 0.000 \nREFERENCE 0,0 \nCLS \nTEXT 320,5,\"2\",0,1,1,\"{{companyName}}\" \nTEXT 310,40,\"2\",0,1,1,\"{{barcode_value}}\" \nBLOCK 310,120,\"0\",0,1,1,\"{{description}}\" \nBARCODE 310,60,\"128\",50,0,0,2,10,\"{{barcode_value}}\" \nTEXT 310,160,\"4\",0,1,1,\"{{unit_price_integer}}\" \nPRINT {{copies}} \nEOP",
        "logging": True,
        "itemCount": 100,
        "enterToSearch": True,
        "useGenericDriver": True,
        "printerName": "TSC_TA200",
        "databaseDriverName": "ODBC Driver 18 for SQL Server",
    }
    try:
        # Ensure the directory exists
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        # Write the JSON data to the file
        with open(file_path, 'w') as json_file:
            json.dump(values, json_file, indent=4)

        print(f"JSON file created successfully at {file_path}")

    except Exception as e:
        print(f"Error creating JSON file: {e}")
