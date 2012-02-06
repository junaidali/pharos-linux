#!/usr/bin/python
# Script Name: setup.py
# Script Function:
#	This script will install pharos remote printing on the system.
#	The following tasks will be performed:
#	1. Install the pharos backend to cups backend directory
#	2. Install the popup scripts to /usr/local/bin/pharospopup
#	3. Install the config file to /usr/local/etc/
#	4. Install the uninstall script to /usr/local/bin/uninstall-pharos
#	3. Setup the users desktop environment to autorun the pharospoup at login
#	4. Create the print queues as defined in printers.conf
#	
# Usage: 
#	$sudo python setup.py
#		This will install pharos remote printing
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

# Script Variables ======================
logFile = os.path.join(os.getcwd(), 'pharos-linux.log')
pharosBackendFileName = 'pharos'

# Functions =============================
def checkPreReqs():
	"""
	Verifies if all program pre-requisites are satisfied. If not then exit the program
	"""
	logger.info('Verifying pre-requisites')
	
	# Check if CUPS is running
	logger.info('checking if cups is available')
	logger.info('Getting list of all running processes')
	try:
		ps = subprocess.check_output(['ps', 'ax'])
	except CalledProcessError as (errCode, errMessage):
		logger.error('Could not get list of running processes')	
		logger.error('Error: %s Message: %s' %(errCode, errMessage))
		sys.exit(1)
		
	processes = ps.split('\n')
	cupsFound = False
	for process in processes:
		if re.search('cups', process):
			logger.info('CUPS is running with details: %s ' %process)
			cupsFound = True
			break			
		else:
			logger.info('Process %s is not cups' %process)
	if cupsFound:
		logger.info('CUPS is installed and running. Can continue')
	else:
		logger.error('CUPS is either not installed or not running. Please make sure CUPS is installed and running before proceeding')
		sys.exit(1)
	
	# Check wxPython	
	logger.info('checking if wxPython is available')
	try:
		import wxPython
	except:
		logger.error('wxPython is not installed. Please make sure wxPython is installed before proceeding')
		sys.exit(1)
	logger.info('wxPython is installed')
	
def installBackend():
	"""
	Install the pharos backend
	"""
	backendDIR = '/usr/lib/cups/backend'
	backendFile = os.path.join(os.getcwd(), pharosBackendFileName)
	
	logger.info('Checking for CUPS backend directory %s' %backendDIR)
	if os.path.exists(backendDIR):
		logger.info('CUPS backend directory %s exists' %backendDIR)
	else:
		logger.error('CUPS backend directory %s not found. Make sure CUPS is correctly setup before proceeding.' %backendDIR)
		sys.exit(1)
	
	logger.info('Copy backend file %s to %s' %(backendFile, backendDIR))
	try:
		shutil.copy(backendFile, backendDIR)
	except IOError as (errCode, errMessage):
		logger.error('Could not copy file %s to %s' %(backendFile, backendDIR))	
		logger.error('Error: %s Message: %s' %(errCode, errMessage))
		sys.exit(1)
	
	if os.path.exists(os.path.join(backendDIR, backendFile)):
		logger.info('Backend file copied successfully')
	else:
		logger.error('Could not copy file %s to %s' %(backendFile, backendDIR))
		sys.exit(1)
	
	# Set execution bits for backend files
	logger.info('Set execution bit on the backend files')
	try:
		chmod = subprocess.check_output(['chmod', '755', os.path.join(backendDIR, pharosBackendFileName), os.path.join(backendDIR, 'lpd')])
	except subprocess.CalledProcessError:
		logger.error('Could not change the execution bit on backend files: %s, %s' %(os.path.join(backendDIR, pharosBackendFileName), os.path.join(backendDIR, 'lpd')))		
		sys.exit(1)
	logger.info('Successfully setup the execution bit on backend files: %s, %s' %(os.path.join(backendDIR, pharosBackendFileName), os.path.join(backendDIR, 'lpd')))
	
def main():
	"""
	The main installer script
	"""
	logger.info('Beginning %s' %sys.argv[0])
	
	# check prerequisites
	checkPreReqs()
	
	# Install backend
	installBackend()
	
	# Install 
	

# Main Script ============================

# Create logger
logger = logging.getLogger('pharos-linux-setup')
logger.setLevel(logging.DEBUG)
# Create file handler
fh = logging.FileHandler(logFile)
fh.setLevel(logging.DEBUG)
# create console handler
ch = logging.StreamHandler()
ch.setLevel(logging.ERROR)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
ch.setFormatter(formatter)
# add loggers
logger.addHandler(fh)
logger.addHandler(ch)

if __name__ == "__main__":
	main()
