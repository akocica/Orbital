#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
	<option value="2056369">Battery</option>
	<option value="2005428">Riverhead</option>
	<option selected="selected" value="1941678">Sunnyside</option>
	<option value="1961750">Treadwell</option>

"""

import cgi
import cgitb; cgitb.enable()

import mechanicalsoup
from bs4 import *
import requests

import location as AL
import json

print("Content-type: text/html")
print("""
<html lang="en" dir="ltr">
<head>
<meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
<title>Orbital</title>
</head>
<body>
"""
)

########################################


def get_passes():

	loginURL = 'https://heavens-above.com/login.aspx'
	satsURL = 'https://www.heavens-above.com/AllSats.aspx'

	br = mechanicalsoup.StatefulBrowser()
	login = br.open(loginURL)
	login.raise_for_status()

	login_form = mechanicalsoup.Form(login.soup.select_one('#aspnetForm'))
	login_form.input({'ctl00$cph1$Login1$UserName': 'akocica@aol.com', 'ctl00$cph1$Login1$Password': 'xxxxx'})
	resp = br.submit(login_form, login.url)
	br.open(satsURL)
	page = br.get_current_page()

	lf = mechanicalsoup.Form(page.select_one('#aspnetForm'))
	lf.set_select({'ctl00$ddlLocation':'1941678'})
	resp = br.submit(lf, satsURL)
	page = br.get_current_page()

	table = page.find("table", class_="standardTable")
	for row in table.findAll("tr"):
		hr = []
		for col in row.findAll("td"):
			hr.append(col.text.strip().encode('ascii', 'ignore').decode())
		print(json.dumps(hr))

########################################


args = cgi.FieldStorage()

lat_arg, lon_arg = AL.getLocation(args)

print("<table>")
get_passes()
print("</table>")
print("</body>")
print("</html>")
