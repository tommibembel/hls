#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

#import RPi.GPIO
import MySQLdb
import locale
import datetime
import time
import os
import ConfigParser
import tabulate
import logging
import math

days = ["montag", "dienstag", "mittwoch", "donnerstag", "freitag", "samstag", "sonntag"]

confparser = ConfigParser.SafeConfigParser()
if os.path.isfile("/etc/hls.conf"):
        confparser.read("/etc/hls.conf")
elif os.path.isfile(os.path.join(os.path.dirname(os.path.realpath(__file__)),"hls.conf")):
        confparser.read(os.path.join(os.path.dirname(os.path.realpath(__file__)),"hls.conf"))
dbhost = confparser.get("database", "dbhost")
dbname = confparser.get("database", "dbname")
dbuser = confparser.get("database", "dbuser")
dbpasswd = confparser.get("database", "dbpasswd")
defpower = int(confparser.get("main", "default_power"))
defprof = confparser.get("main", "default_profile")
pins = confparser._sections["pins"]
pins.pop("__name__", None)
bit = len(pins)
levels = float(math.pow(2,bit)-1)
factor = 100 / levels



def initdb():
  conn = MySQLdb.connect(host=dbhost, user=dbuser, passwd=dbpasswd, db=dbname)
  c = conn.cursor()
  c.execute("DROP TABLE IF EXISTS schedules;")
  c.execute("CREATE TABLE schedules (id int NOT NULL AUTO_INCREMENT, stime time NOT NULL, etime time NOT NULL, power int NOT NULL, dayofweek int NOT NULL, profile int NOT NULL, PRIMARY KEY (id));")
  c.execute("DROP TABLE IF EXISTS profiles;")
  c.execute("CREATE TABLE profiles (id int NOT NULL AUTO_INCREMENT, name text NOT NULL, active int NOT NULL DEFAULT 0, PRIMARY KEY (id));")
  c.execute("INSERT INTO profiles (name, active) VALUES ('manual', 0);")
  c.execute("INSERT INTO profiles (name, active) VALUES ('%s', 1);"%defprof)
  conn.commit()
  conn.close()
  print "Datenbank initialisiert und Tabellen angelegt."

def getentries(dayofweek = None):
  conn = MySQLdb.connect(host=dbhost, user=dbuser, passwd=dbpasswd, db=dbname)
  c = conn.cursor()
  if dayofweek:
    c.execute("SELECT * FROM schedules WHERE dayofweek=%s ORDER BY dayofweek, stime;"%(dayofweek))
  else:
    c.execute("SELECT * FROM schedules ORDER BY dayofweek, stime;")
  res = c.fetchall()
  conn.close()
  return res

def insertschedule(stime = None, etime = None, power = None, dayofweek = None, profile = None):
  printschedules()
  if dayofweek is None:
    dow = raw_input("Bitte den Tag eingeben: ")
    dayofweek = days.index(dow.lower())
  if stime is None:
    stime = raw_input("Bitte die Startzeit eingeben [HH:MM]: ")
  if etime is None:
    etime = raw_input("Bitte die Endzeit eingeben [HH:MM]: ")
  if power is None:
    power = raw_input("Bitte die Leistung eingeben (in %): ")
  if profile is None:
    profile = int(getactiveprofile()["id"])
  conn = MySQLdb.connect(host=dbhost, user=dbuser, passwd=dbpasswd, db=dbname)
  c = conn.cursor()
  c.execute("INSERT INTO schedules (stime, etime, power, dayofweek, profile) VALUES ('%s', '%s', %s, %s, %s );"%(stime, etime, power, dayofweek, profile))
  conn.commit()
  conn.close()

def printschedules(day = None):
  print "Aktives Profil: %s"%getactiveprofile()["name"]
  table = []
  if day is None:
    res = getentries()
  else:
    res = getentries(day)
  for i in range(len(res)):
    t = [int(res[i][0]), days[res[i][4]].capitalize(), str(res[i][1]), str(res[i][2]), int(res[i][3])]
    table.append(t)
  print tabulate.tabulate(table,headers=["ID", "Tag", "Startzeit", "Endzeit", "Leistung %"])

def removeschedule(id=None):
  printschedules()
  if id is None:
    id = int(raw_input("Bitte die zu löschende ID eingeben: "))
  conn = MySQLdb.connect(host=dbhost, user=dbuser, passwd=dbpasswd, db=dbname)
  c = conn.cursor()
  c.execute("DELETE FROM schedules WHERE id=%s"%id)
  conn.commit()
  conn.close()
  printschedules()
  
def printprofiles():
  table = []
  conn = MySQLdb.connect(host=dbhost, user=dbuser, passwd=dbpasswd, db=dbname)
  c = conn.cursor()
  c.execute("SELECT * FROM profiles ORDER BY active DESC, id;")
  res = c.fetchall()
  conn.close()
  for i in range(len(res)):
    t = [res[i][0], res[i][1], res[i][2]] 
    table.append(t) 
  print tabulate.tabulate(table,headers=["ID", "Profilname", "Aktiv"])

def insertprofile(name=None, active=None):
  conn = MySQLdb.connect(host=dbhost, user=dbuser, passwd=dbpasswd, db=dbname)
  c = conn.cursor()
  if name is None:
    name = raw_input("Bitte den Namen für das neue Profil eingeben: ")
  if active is None:
    sa = raw_input("Soll das neue Profil gleich aktiv gesetzt werden? [j|N]: ")
    if sa.lower()[0] == "j":
      active = 1
      c.execute("UPDATE profiles SET active=0 WHERE active=1;")
    else:
      active = 0
  c.execute("INSERT INTO profiles (name, active) VALUES ('%s', %s);"%(name, active))
  conn.commit()
  conn.close()

def removeprofile(id=None):
  printprofiles()
  if id is None:
    id = int(raw_input("Bitte die zu löschende ID eingeben: "))
  conn = MySQLdb.connect(host=dbhost, user=dbuser, passwd=dbpasswd, db=dbname)
  c = conn.cursor()
  c.execute("DELETE FROM profiles WHERE id=%s"%id)
  conn.commit()
  conn.close()
  printprofiles()

def gettime():
  #locale.setlocale(locale.LC_TIME, "de_DE")
  d = datetime.date.today().weekday()
  t = datetime.datetime.now().strftime("%H:%M")
  return (d, t)

def getpower(date, profile=None):
  if profile is None:
    profile = getactiveprofile()["id"]
  d = str(date[0])
  t = str(date[1])
  conn = MySQLdb.connect(host=dbhost, user=dbuser, passwd=dbpasswd, db=dbname)
  c = conn.cursor()
  c.execute("SELECT power, stime FROM schedules WHERE dayofweek=%s AND stime<='%s' AND etime>='%s' AND profile=%s ORDER BY stime DESC;"%(d,t,t,profile))
  res = c.fetchone()
  conn.close()
  if res:
  	return int(res[0])
  else:
	return defpower

def getactiveprofile():
  res = []
  conn = MySQLdb.connect(host=dbhost, user=dbuser, passwd=dbpasswd, db=dbname)
  c = conn.cursor()
  c.execute("SELECT id, name FROM profiles WHERE active=1;")
  row = c.fetchone()
  res = { "id": row[0], "name": row[1]}
  return res

def switchprofile(np=None):
  printprofiles()
  cp = int(getactiveprofile()["id"])
  if np is None:
    np = int(raw_input("Bitte ID des zu aktivierenden Profils eingeben: "))
  conn = MySQLdb.connect(host=dbhost, user=dbuser, passwd=dbpasswd, db=dbname)
  c = conn.cursor()
  c.execute("UPDATE profiles SET active=0 WHERE active=1;")
  c.execute("UPDATE profiles SET active=1 WHERE id=%s;"%np)
  conn.commit()
  conn.close()
  printprofiles()
  
def factorize(val):
  res = val / factor
  return int(res)

def gpio_setup():
  #RPi.GPIO.setmode(RPi.GPIO.BOARD)
  for pin in pins.keys():
    #RPi.GPIO.setup(pins[pin], RPi.GPIO.OUT)
    logging.debug("Setup pin %s"%pin)

def gpio_set(val):
  for p in pins.keys():
    t = math.pow(2,(bit - pins.keys().index(p))-1)
    if (val - t) >= 0:
      #RPi.GPIO.output(pins[p], RPi.GPIO.HIGH)
      logging.debug("Set power to %s."%pins[p])
      val = val - t
    else:
      #RPi.GPIO.output(pins[p], RPi.GPIO.LOW)
      logging.debug("Unset power to %s."%pins[p])

