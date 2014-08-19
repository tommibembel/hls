#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

import functions
import logging
import argparse
import daemon
import ConfigParser
import time
import os

scriptname = os.path.basename(__file__)

confparser = ConfigParser.SafeConfigParser()
if os.path.isfile("/etc/hls.conf"):
        confparser.read("/etc/hls.conf")
elif os.path.isfile(os.path.join(os.path.dirname(os.path.realpath(__file__)),"hls.conf")):
        confparser.read(os.path.join(os.path.dirname(os.path.realpath(__file__)),"hls.conf"))
logfile = confparser.get("main", "logfile")
defprof = confparser.get("main", "default_profile")
defpower = int(confparser.get("main", "default_power"))
sleeptime = int(confparser.get("main", "sleeptime"))
pins = confparser._sections["pins"]
pins.pop("__name__", None)

argparser = argparse.ArgumentParser(description="Haus-Lüfter-Steuerung" , epilog="Programm für die Steuerung eines Lüfters über Zeit- und Leistungsvorgaben.", formatter_class=argparse.ArgumentDefaultsHelpFormatter, conflict_handler='resolve')
exgrp = argparser.add_mutually_exclusive_group()
exgrp.add_argument("--start", help="Startet Daemon.", action="store_true")
exgrp.add_argument("--stop", help="Stoppt Daemon.", action="store_true")
exgrp.add_argument("--initdb", help="Erstellt Datenbank und Tabellen-Schema.", action="store_true")
exgrp.add_argument("-t", "--test", help="Einzelner Lauf.", action="store_true")
exgrp.add_argument("-s", "--schedules", help="Ausgabe der Zeiten.", action="store_true")
exgrp.add_argument("-a", "--addschedule", help="Zeiten hinzufügen.", action="store_true")
exgrp.add_argument("-d", "--delschedule", help="Zeiten löschen.", action="store_true")
exgrp.add_argument("-p", "--profiles", help="Profile Anzeigen.", action="store_true")
exgrp.add_argument("-i", "--insertprofile", help="Profil hinzufügen.", action="store_true")
exgrp.add_argument("-r", "--removeprofile", help="Profil löschen.", action="store_true")
exgrp.add_argument("-c", "--changeprofile", help="Profil ändern.", action="store_true")
argparser.add_argument("-v", "--verbose", help="Setzt verbose Level.", action="count", default=0)
args = argparser.parse_args()


if args.verbose == 0:
  loglvl=logging.ERROR
elif args.verbose == 1:
#  logging.setLevel(logging.WARNING)
#elif args.verbose == 2:
#  logging.setLevel(logging.INFO)
#elif args.verbose >= 3:
  loglvl=logging.DEBUG

logging.basicConfig(filename=logfile ,format='%(asctime)s %(levelname)s %(message)s', level=loglvl)

class daemonize(daemon.Daemon):
  def run(self):
    while 1:
      zeit = functions.gettime()
      res = functions.getpower(zeit)
      res = functions.factorize(res)
      print res
      logging.debug("Get powerlevel of %s"%res)
      functions.gpio_set(res)
      if args.test:
        break
      time.sleep(sleeptime)

d = daemonize("hls.pid")
if args.initdb:
  functions.initdb()
if args.start:
  d.start()
if args.stop:
  d.stop()
if args.test:
  d.run()
if args.schedules:
  functions.printschedules()
if args.delschedule:
  functions.removeschedule()
if args.addschedule:
  functions.insertschedule()
if args.insertprofile:
  functions.insertprofile()
if args.changeprofile:
  functions.switchprofile()
if args.profiles:
  functions.printprofiles()
if args.removeprofile:
  functions.removeprofile()

