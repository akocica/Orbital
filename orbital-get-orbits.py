#!/usr/bin/env python
# coding: utf-8

import location as AL

from bs4 import BeautifulSoup as BS
import mechanicalsoup as MS

from datetime import datetime
from datetime import timedelta
from pytz import timezone
import math
import ephem
import ephem.stars

import numpy as np
import requests
import time

import pickle

lat_arg, lon_arg = AL.getLocation([])

print(lat_arg, lon_arg)
print()

"""
	<option value="2056369">Battery</option>
	<option value="2005428">Riverhead</option>
	<option selected="selected" value="1941678">Sunnyside</option>
	<option value="1961750">Treadwell</option>

"""


def get_ha_passes():

    loginURL = 'https://heavens-above.com/login.aspx'
    satsURL = 'https://www.heavens-above.com/AllSats.aspx'

    br = MS.StatefulBrowser()
    login = br.open(loginURL)
    login.raise_for_status()

    login_form = MS.Form(login.soup.select_one('#aspnetForm'))
    login_form.input({'ctl00$cph1$Login1$UserName': 'akocica@aol.com', 'ctl00$cph1$Login1$Password': 'xxxxx'})
    resp = br.submit(login_form, login.url)
    br.open(satsURL)
    page = br.get_current_page()

    lf = MS.Form(page.select_one('#aspnetForm'))
    lf.set_select({'ctl00$ddlLocation':'1941678'})
    resp = br.submit(lf, satsURL)
    page = br.get_current_page()

    table = page.find("table", class_="standardTable")
    r = []
    for row in table.findAll("tr"):
        hr = []
        satid = ""
        for cell in row.findAll("td"):
            s = cell.text.strip()
            if len(cell.contents):
                c = str(cell.contents[0])
                q = c.find("satid=")
                if q != -1:
                    satid = c.split(';')[1].replace("satid=","").replace("&amp","")
            hr.append(s)
        hr.append(satid)
        if len(hr) > 1 and hr[1].replace('.','',1).replace('-','',1).isdigit() and float(hr[1]) <= 3.0:
            r.append(hr)
    return r

########################################
TimeNow = time.perf_counter() 

ha = []
passes =  get_ha_passes()
distinct_sats = sorted(list(set([p[-1] for p in passes])))
pickle.dump( passes, open( "save.p", "wb" ) )
passes = pickle.load( open( "save.p", "rb" ) )
passes.sort(key=lambda x: x[2])
for p in passes:
    print(p[0].ljust(24), p[1].rjust(5), p[2], p[3].rjust(4), p[4].ljust(4), p[5], p[6].rjust(4), p[7].ljust(4) , p[8], p[9].rjust(4), p[10].ljust(4))
print()


distinct_sats = sorted(list(set([p[-1] for p in passes])))

parse_dict = {}
for sat in distinct_sats:
    url = "https://www.heavens-above.com/orbit.aspx?satid="+sat
    print('\t',url)
    page = requests.get(url)
    soup = BS(page.text, 'html.parser')
    s = soup.find(id="ctl00_cph1_lblLine1").text
    if s:
        ss = soup.find(id="ctl00_cph1_lblLine2").text
        if ss:
            s = s  + '\n' + ss
    parse_dict[sat] = s
    time.sleep(1)
    
tle_dict = {}
for k, v in parse_dict.items():
    v = v.split('\n')
    tle_dict[k] = [k,v[0],v[1]]
sats = []
for tle in list(tle_dict.values()):
    sat = ephem.readtle(tle[0], tle[1], tle[2])
    norad = int(tle[1][2:7])
    name = tle[0].strip()
    label = (name+' '+str(norad)).ljust(16)
    sats.append([norad, name, label, sat])
print()
print(round(time.perf_counter() - TimeNow,1),'seconds',len(list(tle_dict.keys())),'TLEs')


pickle.dump( tle_dict, open( "tle.p", "wb" ) )


tle_dict = pickle.load( open( "tle.p", "rb" ) )


dt = ephem.Date(datetime.utcnow())
dtl = ephem.localtime(dt)
print()
print('Local : ' + datetime.utcnow().strftime("%m/%d %H:%M"))
print('UTC   : ' + dtl.strftime("%m/%d %H:%M"))

obs = ephem.Observer()
obs.date = dt
obs.lon = lon_arg
obs.lat = lat_arg
obs.elevation = 0

sun = ephem.Sun(obs)
sun.compute(obs)
te = ephem.Date(obs.next_rising(sun))

sats = []

for tle in list(tle_dict.values()):
    sat = ephem.readtle(tle[0], tle[1], tle[2])
    norad = int(tle[1][2:7])
    name = tle[0].strip()
    label = (name+' '+str(norad)).ljust(16)
    sats.append([norad, name, label, sat])

print("From  :", ephem.localtime(obs.date).strftime("%m/%d %H:%M"))
print("To    :", ephem.localtime(te).strftime("%m/%d %H:%M"))
print()
calculations = 0
observations = []
for sat in sats:
    t = ephem.Date(datetime.utcnow())
    se = sat[3]
    wasVisible = False
    arc = []
    while t < te :
        obs.date = t        
        sun.compute(obs)
        sun_alt = math.degrees(sun.alt)
        se.compute(obs)
        sat_alt = math.degrees(se.alt)
        sat_az = math.degrees(se.az)
        if sat_alt > 10 and se.eclipsed is False and -18 < sun_alt < -6:
            if not wasVisible:
                    print('\t', sat[0], ephem.localtime(t).strftime("%m/%d %H:%M"), int(sat_az))
            wasVisible = True
            arc.append([sat[0], ephem.localtime(t), sat_az, sat_alt])
        else:
            if wasVisible:
                observations.append(arc)
                arc = []
                wasVisible = False
        calculations = calculations + 1
        t = ephem.Date(t + 5.0 * ephem.second)
print()
print(round(time.perf_counter() - TimeNow,1),'seconds',calculations,'calculations',len(observations),'passes')


pickle.dump( observations, open( "observations.p", "wb" ) )

print(len(observations[0]))
