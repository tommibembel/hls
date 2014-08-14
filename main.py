#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

import os
import logging
import argparse
import time
import datetime
import MySQLdb
import daemon
import locale
import ConfigParser
#import RPi.GPIO

scriptname = os.path.basename(__file__)

bitlvl = float(15)
factor = 100 / bitlvl

confparser = ConfigParser.SafeConfigParser()
if os.path.isfile("/etc/hls.conf"):
        confparser.read("/etc/hls.conf")
elif os.path.isfile(os.path.join(os.path.dirname(os.path.realpath(__file__)),"hls.conf")):
        confparser.read(os.path.join(os.path.dirname(os.path.realpath(__file__)),"hls.conf"))
logfile = confparser.get("main", "logfile")
defprof = confparser.get("main", "default_profile")
sleeptime = int(confparser.get("main", "sleeptime"))
dbhost = confparser.get("database", "dbhost")
dbname = confparser.get("database", "dbname")
dbuser = confparser.get("database", "dbuser")
dbpasswd = confparser.get("database", "dbpasswd")
pins = confparser._sections["pins"]
pins.pop("__name__", None)

argparser = argparse.ArgumentParser(description="Haus-Lüfter-Steuerung" , epilog="Programm für die Steuerung eines Lüfters über Zeit- und Leistungsvorgaben.", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
argparser.add_argument("-i", "--initdb", help="Erstellt Datenbank und Tabellen-Schema.", action="store_true")
argparser.add_argument("-d", "--daemonize", help="Startet Daemon.", action="store_true")
argparser.add_argument("-k", "--kill", help="Stoppt Daemon.", action="store_true")
argparser.add_argument("-t", "--test", help="Einzelner Lauf.", action="store_true")
argparser.add_argument("-v", "--verbose", help="Setzt verbose Level.", action="count", default=0)
args = argparser.parse_args()


logger = logging.getLogger(scriptname)
hdlr = logging.FileHandler(logfile)
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
hdlr.setFormatter(formatter)
logger.addHandler(hdlr)
if args.verbose == 0:
  logger.setLevel(logging.ERROR)
elif args.verbose == 1:
#  logger.setLevel(logging.WARNING)
#elif args.verbose == 2:
#  logger.setLevel(logging.INFO)
#elif args.verbose >= 3:
  logger.setLevel(logging.DEBUG)

def initdb():
  conn = MySQLdb.connect(host=dbhost, user=dbuser, passwd=dbpasswd, db=dbname)
  c = conn.cursor()
  c.execute("DROP TABLE IF EXISTS schedules;")
  c.execute("CREATE TABLE schedules (stime time, etime time, power int, dayofweek int, profile int);")
  c.execute("DROP TABLE IF EXISTS profiles;")
  c.execute("CREATE TABLE profiles (id int, name text, active int);")
  c.execute("INSERT INTO profiles VALUES (1, 'manual', 0);")
  c.execute("INSERT INTO profiles VALUES (2, '%s', 1);"%defprof)
  conn.commit()
  conn.close()
  print "Datenbank initialisiert und Tabellen angelegt."

def gettime():
  #locale.setlocale(locale.LC_TIME, "de_DE")
  d = datetime.date.today().weekday()
  t = datetime.datetime.now().strftime("%H:%M")
  return (d, t)

def getpower(date, profile):
  d = str(date[0])
  t = str(date[1])
  conn = MySQLdb.connect(host=dbhost, user=dbuser, passwd=dbpasswd, db=dbname)
  c = conn.cursor()
  print "SELECT power FROM schedules WHERE dayofweek=%s AND stime<='%s' AND etime>='%s' AND profile=%s;"%(d,t,t,profile)
  c.execute("SELECT power FROM schedules WHERE dayofweek=%s AND stime<='%s' AND etime>='%s' AND profile=%s;"%(d,t,t,profile))
  res = c.fetchall()
  conn.close()
  return int(res[0][0])

def getactiveprofile():
  conn = MySQLdb.connect(host=dbhost, user=dbuser, passwd=dbpasswd, db=dbname)
  c = conn.cursor()
  c.execute("SELECT id FROM profiles WHERE active=1;")
  res = c.fetchall()
  conn.close()
  return int(res[0][0])

def factorize(val):
  res = val / factor
  return int(res)

def gpio_setup():
  RPi.GPIO.setmode(RPi.GPIO.BOARD)
  for pin in pins.keys():
    RPi.GPIO.setup(pins[pin], RPi.GPIO.OUT)

def gpio_set(val):
  if (val - 8) >= 0:
    RPi.GPIO.output(pins["8"], RPi.GPIO.HIGH)
    logger.debug("Set power to %s."%pins["8"])
    val = val - 8
  else:
    RPi.GPIO.output(pins["8"], RPi.GPIO.LOW)
    logger.debug("Unset power to %s."%pins["8"])
  if (val - 4) >= 0:
    RPi.GPIO.output(pins["8"], RPi.GPIO.HIGH)
    logger.debug("Set power to %s."%pins["4"])
    val = val - 4
  else:
    RPi.GPIO.output(pins["8"], RPi.GPIO.LOW)
    logger.debug("Unset power to %s."%pins["4"])
  if (val - 2) >= 0:
    RPi.GPIO.output(pins["8"], RPi.GPIO.HIGH)
    logger.debug("Set power to %s."%pins["2"])
    val = val - 2
  else:
    RPi.GPIO.output(pins["8"], RPi.GPIO.LOW)
    logger.debug("Unset power to %s."%pins["2"])
  if (val - 1) >= 0:
    RPi.GPIO.output(pins["8"], RPi.GPIO.HIGH)
    logger.debug("Set power to %s."%pins["1"])
    val = val - 1
  else:
    RPi.GPIO.output(pins["8"], RPi.GPIO.LOW)
    logger.debug("Unset power to %s."%pins["1"])
  

class daemonize(daemon.Daemon):
  def run(self):
    while 1:
      zeit = gettime()
      res = getpower(zeit,getactiveprofile())
      res = factorize(res)
      print res
      logger.debug("Get powerlevel of %s"%res)
      gpio_set(res)
      time.sleep(sleeptime)
      if args.test:
        break

d = daemonize("hls.pid")
if args.initdb:
  initdb()
if args.daemonize:
  d.start()
if args.kill:
  d.stop()
if args.test:
  d.run()

