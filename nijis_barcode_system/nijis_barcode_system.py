import json
import os
import subprocess
import time

import requests
from flask import Flask, render_template, request
import secrets.config as config

import barcode
from PIL import Image, ImageDraw, ImageFont

import brother_ql
from brother_ql.raster import BrotherQLRaster
from brother_ql.backends.helpers import send
PRINTER_IDENTIFIER = 'usb://0x04f9:0x2028'

token = config.nijis_api_key

BASE_DIR = "~/Documents/jam_labels"

app = Flask(__name__)

#url_prefix = "http://127.0.0.1:5000"
#url_prefix = "https://workshops.niraspberryjam.com"
url_prefix = "https://s.youthzone.xyz"

equipment_url = url_prefix + "/api/equipment/" + str(config.nijis_api_key)
equipment_groups_url = url_prefix + "/api/equipment_groups/" + str(config.nijis_api_key)
add_equipment_entries_url =url_prefix + "/api/add_equipment_entries/" + str(config.nijis_api_key)
add_equipment_url =url_prefix + "/api/add_equipment/"


@app.route("/")
def home():
    print(equipment_url)
    equipment = requests.get(equipment_url).json()
    equipment_groups = requests.get(equipment_groups_url).json()
    return render_template("index.html", equipment=equipment, equipment_groups=equipment_groups, equipment_json=json.dumps(equipment))


@app.route("/print_labels", methods=['POST'])
def print_labels():
    equipment_id = int(request.form['equipment_id'])
    quantity = int(request.form['quantity'])
    label_data = requests.post(add_equipment_entries_url, data={"equipment_id":equipment_id, "quantity":quantity}).json()
    for label in label_data:
        create_label_image(label[0], label[1])
        #create_label_image(label[0], label[1])
        #print_label(label[0], label[1])
    return ""


@app.route("/reprint_label", methods=["POST"])
def reprint_label():
    entry_id = int(request.form['entry_id'])
    entry_code = (request.form['entry_code'])
    create_label_image(entry_id, entry_code)
    #print_label(entry_id, entry_code)
    return ""


@app.route("/add_equipment", methods=["POST"])
def add_equipment():
    equipment_name = request.form['equipment_name']
    equipment_code = request.form['equipment_code']
    equipment_group_id = request.form['equipment_group_id']
    if requests.post(add_equipment_url, data={"token": token, "equipment_name": equipment_name, "equipment_code": equipment_code, "equipment_group_id": equipment_group_id}):
        return ""


def print_label(equipment_entry_id, equipment_entry_number):
    print("Printing label with barcode {} and entry_number of {}".format(equipment_entry_id, equipment_entry_number))
    #os.chdir(BASE_DIR)
    barcode_filename = "{}/out.png".format(BASE_DIR)
    subprocess.run(["zint", "--scale", "10", "-d", str(equipment_entry_id), "-b", "38", "-o", barcode_filename])
    find_replace_svg_file([["BARCODE_PATH", barcode_filename], ["ITEMCODE", equipment_entry_number]])
    subprocess.call(["inkscape", "to_print.svg", "--export-pdf=to_print.pdf"])
    
    #subprocess.call(["lp", "-d", "Brother-QL-570-barcode29", "to_print.pdf", "-o", "media=3B"])
    send_to_printer("to_print.pdf")


def generate_barcode(data):
    #img = qrcode.make(URL, error_correction=qrcode.constants.ERROR_CORRECT_M)
    #path = barcode.
    barcode_filename = "out.png"
    subprocess.run(["zint", "--scale", "10", "-d", str(data), "-b", "38", "-o", barcode_filename])
    im = Image.open(barcode_filename)
    return im


def create_label_image(equipment_entry_id, equipment_entry_number):
    barcode_image = generate_barcode(equipment_entry_id)

    name_font = ImageFont.truetype("arial.ttf", 30)
    jam_font = ImageFont.truetype("arial.ttf", 27)
    qr_font = ImageFont.truetype("arial.ttf", 22)
    #img = Image.new('L', (500, 306), color='white') # Continuous labels
    img = Image.new('L', (991, 306), color='white') # 29x90 labels

    d = ImageDraw.Draw(img)
    d.text((190, 215), equipment_entry_number, fill="black", font=name_font)
    #d.text((20, 60), "Order ID : {} -- {}".format("order_id", "ticket_name"), fill="black", font=jam_font)
    img.paste(barcode_image.resize((400, 210), Image.ANTIALIAS), (50, 0))
    #d.text((220, 240), "NI Raspberry Jam", fill="black", font=jam_font)
    d.text((86, 245), "Northern Ireland Raspberry Jam", fill="black", font=qr_font)
    d.text((126, 270), "info@niraspberryjam.com", fill="black", font=qr_font)

    img.save('generated_badge.png')
    time.sleep(0.1)
    send_to_printer('generated_badge.png')


def print_label_2(equipment_entry_id, equipment_entry_number):
    print("Printing label with barcode {} and entry_number of {}".format(equipment_entry_id, equipment_entry_number))
    


def send_to_printer(path):
    printer = BrotherQLRaster('QL-570')
    #print_data = brother_ql.brother_ql_create.convert(printer, [path], '29', dither=True, rotate="90", hq=True)   # Continuous labels
    print_data = brother_ql.brother_ql_create.convert(printer, [path], '29x90', dither=True, rotate="90", hq=True) # 29x90 labels
    send(print_data, PRINTER_IDENTIFIER)
    

def find_replace_svg_file(find_replace, template_filename="template2.svg", output_filename="to_print.svg"):
    new_file = []
    with open(template_filename) as f:
        for line in f.readlines():
            new_file.append(line)

    for item_pair in find_replace:
        for line_num in range(0, len(new_file)):
            new_file[line_num] = new_file[line_num].replace(item_pair[0], item_pair[1])
    with open(output_filename, "w") as nf:
        nf.writelines(new_file)


if __name__ == '__main__':
    app.run(port=5001)