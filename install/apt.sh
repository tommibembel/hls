#!/bin/bash
apt-get update
apt-get -y upgrade
apt-get -y install mysql-server python-mysqldb python-mysqldb-dbg python-rpi.gpio python-dev
# No NEED of following files
apt-get -y install vim
update-alternatives --set editor /usr/bin/vim.tiny
