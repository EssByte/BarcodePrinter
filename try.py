import win32print

def send_to_printer(printer_name, raw_data):
    # Open the printer
    printer = win32print.OpenPrinter(printer_name)
    try:
        # Start a print job
        job_info = ("Print Job", None, "RAW")
        job_id = win32print.StartDocPrinter(printer, 1, job_info)
        
        # Start a new page
        win32print.StartPagePrinter(printer)
        # Send raw data to the printer
        win32print.WritePrinter(printer, raw_data.encode())
        
        # End the page and the job
        win32print.EndPagePrinter(printer)
        win32print.EndDocPrinter(printer)
    finally:
        # Close the printer connection
        win32print.ClosePrinter(printer)

# Example usage
printer_name = win32print.GetDefaultPrinter()
raw_data = """
SPEED 2.0 
DENSITY 7 
DIRECTION 0 
SIZE 35MM,25MM 
OFFSET 0.000 
REFERENCE 0,0 
CLS 
TEXT 320,15,"2",0,1,1,"companyName" 
TEXT 310,40,"2",0,1,1,"12345" 
TEXT 310,120,"0",0,1,1,descrkjldfnioregnskjfbldgblwiption
BARCODE 310,60,"128",50,0,0,2,10,"12345" 
TEXT 310,160,"4",0,1,1,"RM20.00" 
PRINT 1
EOP
"""
send_to_printer("TSC_TA200", raw_data)
