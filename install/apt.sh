#!/bin/bash
apt-get update
apt-get -y upgrade
apt-get -y install mysql-server python-mysqldb python-mysqldb-dbg


apt-get -y install vim
update-alternatives --set editor /usr/bin/vim.tiny
