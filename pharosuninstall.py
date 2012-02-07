#!/usr/bin/python
# Script Name: uninstall-pharos.py
# Script Function:
#	This script will uninstall pharos remote printing from the system.
#	The following tasks will be performed:
#	1. Remove the pharos backend from cups backend directory
#	2. Remove the popup scripts from /usr/local/bin/pharospopup
#	3. Remove the config file from /usr/local/etc/
#	4. Remove the uninstall script from /usr/local/bin/
#	5. Remove the users desktop environment autorun settings for running pharospoup at login
#	6. Delete the print queues that use pharos backend
#	
# Usage: 
#	$sudo python uninstall-pharos
#		This will uninstall the pharos remote printing
#
# Author: Junaid Ali
# Version: 1.0

# Imports ===============================
import os
import sys
import logging
import subprocess
import re
import shutil
import ConfigParser

# Script Variables ======================
logFile = '/tmp/pharosuninstall.log'

# Functions =============================
def uninstall():
	""""
	The main function
	"""
	logger.info('Beginning pharos uninstallation')
	
	
	
	# Quit
	sys.exit(0)
	


# Main Script ============================

# Create logger
logger = logging.getLogger('pharos-uninstaller')
logger.setLevel(logging.DEBUG)
# Create file handler
fh = logging.FileHandler(logFile)
fh.setLevel(logging.DEBUG)
# create console handler
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
ch.setFormatter(formatter)
# add loggers
logger.addHandler(fh)
logger.addHandler(ch)

if __name__ == "__main__":
	uninstall()
