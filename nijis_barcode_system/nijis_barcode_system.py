import json
import os
import subprocess

import requests
from flask import Flask, render_template, request
import secrets.config as config

token = config.nijis_api_key

BASE_DIR = "~/Documents/jam_labels"

app = Flask(__name__)

dev_url_prefix = "http://127.0.0.1:5000"
url_prefix = "https://workshops.niraspberryjam.com"

equipment_url = dev_url_prefix + "/api/equipment/" + str(config.nijis_api_key)
equipment_groups_url = dev_url_prefix + "/api/equipment_groups/" + str(config.nijis_api_key)
add_equipment_entries_url =dev_url_prefix + "/api/add_equipment_entries/" + str(config.nijis_api_key)
add_equipment_url =dev_url_prefix + "/api/add_equipment/"


@app.route("/")
def home():
    equipment = requests.get(equipment_url).json()
    equipment_groups = requests.get(equipment_groups_url).json()
    return render_template("index.html", equipment=equipment, equipment_groups=equipment_groups, equipment_json=json.dumps(equipment))


@app.route("/print_labels", methods=['POST'])
def print_labels():
    equipment_id = int(request.form['equipment_id'])
    quantity = int(request.form['quantity'])
    label_data = requests.post(add_equipment_entries_url, data={"equipment_id":equipment_id, "quantity":quantity}).json()
    for label in label_data:
        print_label(label[0], label[1])
    return ""


@app.route("/reprint_label", methods=["POST"])
def reprint_label():
    entry_id = int(request.form['entry_id'])
    entry_code = (request.form['entry_code'])
    print_label(entry_id, entry_code)
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
    os.chdir(BASE_DIR)
    barcode_filename = "{}/out.png".format(BASE_DIR)
    subprocess.run(["zint", "--scale", "10", "-d", str(equipment_entry_id), "-b", "38", "-o", barcode_filename])
    find_replace_svg_file([["BARCODE_PATH", barcode_filename], ["ITEMCODE", equipment_entry_number]])
    subprocess.call(["inkscape", "to_print.svg", "--export-pdf=to_print.pdf"])
    subprocess.call(["lp", "-d", "Brother-QL-570-barcode29", "to_print.pdf", "-o", "media=3B"])


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