from app import app
from flask import request, redirect
from flask.templating import render_template
import urllib
from werkzeug.utils import redirect
from werkzeug.utils import secure_filename
import xml.etree.ElementTree as ET
import pandas as pd
from lxml import etree
import calendar
import time
import re
import math
import io


app.config["ALLOWED_FILE_EXTENSIONS"] = {"XML", "CSV", "XLSX", "xlsx"}
app.config['MAX_CONTENT_LENGTH'] = 700 * 1024 * 1024
xmlDocument = r'instance/uploads/'

def get_namespace(element):
    m = re.match('\{.*\}', element.tag)
    return m.group(0) if m else ''

def allowed_file(filename):
    if not "." in filename:
        return False
    # for the extension
    ext = filename.rsplit(".", 1)[1]
    if ext.upper() in app.config["ALLOWED_FILE_EXTENSIONS"]:
        return True
    else:
        return False

def allowed_file_filesize(filesize):
    if int(filesize) <= app.config["MAX_FILE_FILESIZE"]:
        return True
    else:
        return False

def upload():
    if request.method == "POST":
        if request.files:
            if "filesize" in request.cookies:
                if not allowed_file_filesize(request.cookies["filesize"]):
                    print("Filesize exceeded maximum limit")
                    return redirect(request.url)
            file = request.files["file"]

            if file.filename == "":
                print("No filename")
                return redirect(request.url)
            if allowed_file(file.filename):
                filename = secure_filename(file.filename)
                os.makedirs(os.path.join(app.instance_path, 'uploads'), exist_ok=True)
                file.save(os.path.join(app.instance_path, 'uploads', secure_filename(filename)))
                print("File Saved")
                return redirect(url_for('upload_file',filename=filename))
            else:
                print("That file extension is not allowed.")
                return redirect(request.url)

xmlDocument = r'instance/uploads/'

def xml_to_dataframe(xmlDocument):
    class_data = []
    data = []

    for event,elem in ET.iterparse(xmlDocument, events=('start', 'end')):
        tag = extract_local_tag(elem.tag)
        if event=='start' and tag=='managedObject':
            class_data=[elem.get('class').strip(),elem.get('version').strip(),elem.get('distName').strip(),elem.get('id').strip()]
        if event=='start' and tag=='p':
            data.append(class_data+[elem.get('name'),elem.text])
    df = pd.DataFrame(data,columns=['class','version','distName','id','parameter','value'])
    return df

def updateXML(xmlDocument,class_,sites,param_dict):
    param_for_list = {}

    for k,v in param_dict.items():
        if '-' in k:
            param_for_list[k] = v

    tree = etree.parse(xmlDocument)
    root =  tree.getroot().findall('*')[0]
    relevent = []
    for elem in tree.findall('//{raml20.xsd}managedObject'):
            site = elem.get('distName').split('/')[1].split('-')[1].strip()
            if elem.attrib['class'].strip().lower()== class_  and (site in sites):
                relevent.append(elem)
            else:
                root.remove(elem)
    for elem in relevent:
            for p in elem.findall('{raml20.xsd}p'):
                if(p.get('name').strip().lower() in param_dict):
                    p.text = param_dict.get(p.get('name').strip().lower())
                else:
                    elem.remove(p)
            # For handling list items
            for param,value in param_for_list.items():
                items = param.split('-')
                list_name = items[0].strip().lower()
                item_name = items[2].strip().lower()
                try:
                    item_number = int(items[1])
                except(ValueError):
                    # case of all
                    item_number = items[1].strip().lower()
                for i in elem.findall('{raml20.xsd}list'):
                    if i.get('name').strip().lower()==list_name:
                        # if a param from all items of a list need to be updated
                        if item_number == "all":
                            for item in i.findall('{raml20.xsd}item'):
                                for p in item.findall('{raml20.xsd}p'):
                                    if (p.get('name').strip().lower() == item_name.strip().lower()):
                                        p.text = value
                                    if p.get('name').strip().lower() not in [x.split('-')[2].strip().lower() for x in list(param_for_list.keys())]:
                                        item.remove(p)
                        # If a particular index of item needs to be updated
                        else:
                            try:
                                for p in (i.getchildren()[item_number-1].findall('{raml20.xsd}p')):
                                    if (p.get('name').strip().lower() == item_name.strip().lower()):
                                        p.text = value
                                    if p.get('name').strip().lower() not in [x.split('-')[2].strip().lower() for x in list(param_for_list.keys())]:
                                        i.getchildren()[item_number-1].remove(p)
                            except(IndexError):
                                # Remove list if item number is wrong
                                print('Index Error for list name:{}'.format(i.get('name')))
                    if (i.get('name').strip().lower() not in [x.split('-')[0].strip().lower() for x in list(param_for_list.keys())]):
                        elem.remove(i)
    et = etree.ElementTree(tree.getroot())
    # print(etree.tostring(tree,encoding="unicode", pretty_print=True))
    et.write('app/download/download.xml', pretty_print=True)
    return

@app.route('/download/download.xml', methods=["GET"])
def plot_xml():
    path = 'app/download/download.xml'
    return_data = io.BytesIO()
    with open(path, 'rb') as fo:
        return_data.write(fo.read())
    # (after writing, cursor will be at last byte, so move it to start)
    return_data.seek(0)
    os.remove(path)
    clear_uploads('instance/uploads/')
    print("File Cleared!")
    return send_file(return_data,
                     mimetype='text/xml',
                     attachment_filename='result.xml',
                     as_attachment=True)
