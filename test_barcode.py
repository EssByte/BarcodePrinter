from modules.ImagePrinter import ImagePrinter

printer = ImagePrinter()
print("Rendering design layout:")
im = printer.render_fun_bake_label({'description': 'Test', 'barcode_value': '12345678', 'remark': '', 'unit_price_integer': '1.00', 'net_weight': '', 'batch': ''})
print("Done.")

# We should also try with an empty barcode or something?
im2 = printer.render_fun_bake_label({'description': 'Test', 'barcode_value': '', 'remark': '', 'unit_price_integer': '1.00', 'net_weight': '', 'batch': ''})
