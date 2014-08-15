#!/bin/bash

sudo apt-get update

sudo apt-get install -y python-pip

pip install sympy

pip install httplib2

sudo apt-get install -y python2.7-mysqldb

# sudo apt-get install mysql-server

pip install mysql-connector-python --allow-external mysql-connector-python
