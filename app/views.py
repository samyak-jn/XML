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


