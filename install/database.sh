#!/bin/bash
mysql_secure_installation
mysql -uroot -p << mysql_database_setup
