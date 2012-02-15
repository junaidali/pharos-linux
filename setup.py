#!/usr/bin/python
# Script Name: setup.py
# Script Function:
#	This script will install pharos remote printing on the system.
#	The following tasks will be performed:
#	1. Install the pharos backend to cups backend directory
#	2. Install the popup scripts to /usr/local/bin/pharospopup
#	3. Install the config file to /usr/local/etc/
#	4. Install the uninstall script to /usr/local/bin/uninstall-pharos
#	5. Setup the users desktop environment to autorun the pharospoup at login
#	6. Create the print queues as defined in printers.conf
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
import ConfigParser
import curses

# Script Variables ======================
logFile = os.path.join(os.getcwd(), 'pharos-linux.log')
pharosBackendFileName = 'pharos'
pharosPopupServerFileName = 'pharospopup'
pharosConfigFileName = 'pharos.conf'
printersConfigFile = os.path.join(os.getcwd(), 'printers.conf')
uninstallFile = 'pharos-uninstall'

popupServerInstallDIR = '/usr/local/bin'
pharosConfigInstallDIR = '/usr/local/etc'
pharosUninstallerDIR = '/usr/local/bin'
uninstallerSharedLibraryDIR = '/usr/local/lib/pharos'
pharosLogDIR = '/var/log/pharos'
programLogFiles = ['pharos.log', 'pharospopup.log']
uninstallerSharedLibraryFiles = ['pharosuninstall.pyc', 'printerutils.pyc', 'processutils.pyc']

# Regular Expressions
gnomeWindowManagerRegularExpression = 'gnome|unity'
kdeWindowManagerRegularExpression = 'kde'

# Functions =============================
def checkPreReqs():
	"""
	Verifies if all program pre-requisites are satisfied. If not then exit the program
	"""
	logger.info('Verifying pre-requisites')
	
	# Check if CUPS is running
	logger.info('checking if cups is available')
	if processUtils.isProcessRunning('cups'):
		logger.info('CUPS is installed and running. Can continue')
	else:
		logger.error('CUPS is either not installed or not running. Please make sure CUPS is installed and running before proceeding')
		uninstallAndExit()
	
	# Check wxPython	
	logger.info('checking if wxPython is available')
	try:
		import wxPython
	except:
		logger.error('wxPython is not installed. Please make sure wxPython is installed before proceeding')
		uninstallAndExit()
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
		uninstallAndExit()
	
	logger.info('Copy backend file %s to %s' %(backendFile, backendDIR))
	try:
		shutil.copy(backendFile, backendDIR)
	except IOError as (errCode, errMessage):
		logger.error('Could not copy file %s to %s' %(backendFile, backendDIR))	
		logger.error('Error: %s Message: %s' %(errCode, errMessage))
		uninstallAndExit()
	
	if os.path.exists(os.path.join(backendDIR, backendFile)):
		logger.info('Backend file copied successfully')
	else:
		logger.error('Could not copy file %s to %s' %(backendFile, backendDIR))
		uninstallAndExit()
	
	# Set execution bits for backend files
	logger.info('Set execution bit on the backend files')
	try:
		chmod = subprocess.check_output(['chmod', '755', os.path.join(backendDIR, pharosBackendFileName), os.path.join(backendDIR, 'lpd')])
	except subprocess.CalledProcessError:
		logger.error('Could not change the execution bit on backend files: %s, %s' %(os.path.join(backendDIR, pharosBackendFileName), os.path.join(backendDIR, 'lpd')))		
		uninstallAndExit()
	logger.info('Successfully setup the execution bit on backend files: %s, %s' %(os.path.join(backendDIR, pharosBackendFileName), os.path.join(backendDIR, 'lpd')))

def installPopupServer():
	"""
	Installs the popup server files
	"""
	logger.info('Installing poup server files')
	popupExecutable = os.path.join(os.getcwd(), pharosPopupServerFileName)
	pharosConfig = os.path.join(os.getcwd(),pharosConfigFileName)
	 
	try:
		logger.info('Trying to copy %s to %s' %(popupExecutable, popupServerInstallDIR))
		shutil.copy(popupExecutable, popupServerInstallDIR)
		logger.info('Successfully copied %s to %s' %(popupExecutable, popupServerInstallDIR))		
	except IOError as (errCode, errMessage):
		logger.error('Could not copy file %s to %s' %(pharosConfig, pharosConfigInstallDIR))
		logger.error('Error: %s Message: %s' %(errCode, errMessage))
		uninstallAndExit()
	
	try:
		logger.info('Trying to copy %s to %s' %(pharosConfig, pharosConfigInstallDIR))
		shutil.copy(pharosConfig, pharosConfigInstallDIR)
		logger.info('Successfully copied %s to %s' %(pharosConfig, pharosConfigInstallDIR))
	except IOError as (errCode, errMessage):
		logger.error('Could not copy file %s to %s' %(pharosConfig, pharosConfigInstallDIR))
		logger.error('Error: %s Message: %s' %(errCode, errMessage))
		uninstallAndExit()
	
def addPopupServerToGnomeSession():
	"""
	Adds the popup server to gnome session
	"""
	gnomeAutoStartFile = """
[Desktop Entry]
Type=Application
Exec=%s
Hidden=false
X-GNOME-Autostart-enabled=true
Name[en_US]=PharosPopup
Name=PharosPopup
Comment[en_US]=Pharos Popup Server
Comment=Pharos Popup Server
""" %(os.path.join(popupServerInstallDIR, pharosPopupServerFileName))
	
	logger.info('Getting list of current users')
	currentUsers = os.listdir('/home')	
	for user in currentUsers:
		logger.info('Adding autostart file to user %s' %user)
		autoStartDIR = os.path.join('/home', user, '.config', 'autostart')
		logger.info('Checking if directory %s exists' %autoStartDIR)
		if not os.path.exists(autoStartDIR):
			logger.info('Creating autostart directory %s' %autoStartDIR)
			os.makedirs(autoStartDIR)			
		else:
			logger.info('Autostart directory %s already exists' %autoStartDIR)
		
		if os.path.exists(autoStartDIR):			
			autoStartFile = os.path.join('/home', user, '.config', 'autostart', 'pharospopup.desktop')
			# Delete old file if it exists
			if os.path.exists(autoStartFile):
				logger.info('Deleted old version of autostart file: %s' %autoStartFile)
				os.remove(autoStartFile)
			# create new file
			autoStartFH = open(autoStartFile, 'w')
			autoStartFH.write(gnomeAutoStartFile)
			autoStartFH.close()
			logger.info('Successfully added autostart for %s user' %user)
		else:
			logger.warn('Autostart file %s could not be created' %autoStartFile)
	
	# Update the autostart file for root
	logger.info('Updating autostart file for root')
	rootAutoStartDIR =  os.path.join('/root', '.config', 'autostart')
	rootAutoStartFile = os.path.join('/root', '.config', 'autostart', 'pharospopup.desktop')
	if not os.path.exists(rootAutoStartDIR):
		logger.info('Creating autostart directory %s' %rootAutoStartDIR)
		os.makedirs(rootAutoStartDIR)
	if os.path.exists(rootAutoStartFile):
		logger.info('Deleting old version of skel autostart file: %s' %rootAutoStartFile)
		os.remove(rootAutoStartFile)
		
	rootAutoStartFH = open(rootAutoStartFile, 'w')
	rootAutoStartFH.write(gnomeAutoStartFile)
	rootAutoStartFH.close()
	logger.info('Successfully added autostart to root user')
		
	# Update the autostart file in skel
	logger.info('Updating autostart file for future users')
	skelAutoStartDIR = os.path.join('/etc/', 'skel', '.config', 'autostart')
	skelAutoStartFile = os.path.join('/etc/', 'skel', '.config', 'autostart', 'pharospopup.desktop')
	
	if not os.path.exists(skelAutoStartDIR):
		logger.info('Creating autostart directory %s' %skelAutoStartDIR)
		os.makedirs(skelAutoStartDIR)
	
	if os.path.exists(skelAutoStartFile):
		logger.info('Deleting old version of skel autostart file: %s' %skelAutoStartFile)
		os.remove(skelAutoStartFile)
		
	skelAutoStartFH = open(skelAutoStartFile, 'w')
	skelAutoStartFH.write(gnomeAutoStartFile)
	skelAutoStartFH.close()
	logger.info('Successfully added autostart in skel for future users')

def addPopupServerToKDESession():
	"""
	Adds autostart option for KDE desktops
	"""
	returnCode = True
	popupExecutablePath = os.path.join(popupServerInstallDIR, pharosPopupServerFileName)
	logger.info('Adding autostart file for KDE')
	logger.info('Getting list of current users')
	
	currentUsers = os.listdir('/home')	
	for user in currentUsers:
		logger.info('Adding autostart file to user %s' %user)
		autoStartDIR = os.path.join('/home', user, '.kde', 'Autostart')
		logger.info('Checking if directory %s exists' %autoStartDIR)
		if not os.path.exists(autoStartDIR):
			logger.info('Creating autostart directory %s' %autoStartDIR)
			os.makedirs(autoStartDIR)			
		else:
			logger.info('Autostart directory %s already exists' %autoStartDIR)
		
		if os.path.exists(autoStartDIR):			
			autoStartFile = os.path.join(autoStartDIR, 'pharospopup')
			# Delete old file if it exists
			if os.path.exists(autoStartFile):
				logger.info('Deleted old version of autostart file: %s' %autoStartFile)
				os.remove(autoStartFile)
			# create new link
			lnCommand = ['ln', '-s', popupExecutablePath, autoStartFile]
			logger.info('Creating autostart file using command %s' %lnCommand)
			try:
				subprocess.call(lnCommand)
				logger.info('Successfully added autostart for %s user' %user)
			except subprocess.CalledProcessError:
				logger.error('Could not create autostart file for user %s' %user)
				returnCode = False
		else:
			logger.warn('Autostart file %s could not be created' %autoStartFile)
	
	# Create autostart file for root
	rootAutoStartDIR = os.path.join('/root', '.kde', 'Autostart')
	rootAutoStartFile = os.path.join(rootAutoStartDIR, 'pharospopup')
	logger.info('Adding autostart file for root')
	if not os.path.exists(rootAutoStartDIR):
		logger.info('Creating autostart directory %s' %rootAutoStartDIR)
		os.makedirs(rootAutoStartDIR)			
	else:
		logger.info('Autostart directory %s already exists' %rootAutoStartDIR)
	
	lnCommand = ['ln', '-s', popupExecutablePath, rootAutoStartFile]
	logger.info('Creating autostart file using command %s' %lnCommand)
	try:
		subprocess.call(lnCommand)
		logger.info('Successfully added autostart for root user')
	except subprocess.CalledProcessError:
		logger.error('Could not create autostart file for root user')
		returnCode = False
	
	# Create autostart file for future users
	futureUsersAutoStartDIR = os.path.join('/etc/skel', '.kde', 'Autostart')
	futureUsersAutoStartFile = os.path.join(futureUsersAutoStartDIR, 'pharospopup')
	if not os.path.exists(futureUsersAutoStartDIR):
		logger.info('Creating autostart directory %s' %futureUsersAutoStartDIR)
		os.makedirs(futureUsersAutoStartDIR)			
	else:
		logger.info('Autostart directory %s already exists' %futureUsersAutoStartDIR)		
	
	lnCommand = ['ln', '-s', popupExecutablePath, futureUsersAutoStartFile]
	logger.info('Creating autostart file using command %s' %lnCommand)
	try:
		subprocess.call(lnCommand)
		logger.info('Successfully added autostart for future users')
	except subprocess.CalledProcessError:
		logger.error('Could not create autostart file for future users')
		returnCode = False
	
	return returnCode
	
def addPopupServerToLogin():
	""""
	Add the popup server to all users.
	Add the popup server for all future users
	"""	
	logger.info('Analyzing desktop environment')
	if processUtils.isProcessRunning('gnome'):
		logger.info('User is using gnome window manager')
		addPopupServerToGnomeSession()		
	elif processUtils.isProcessRunning('kde'):
		logger.info('User is using kde Window Manager')
		addPopupServerToKDESession()
	else:
		logger.warn('Users window manager is not recognized. Could not setup login scripts for popupserver. Please use your window manager to add startup script %s' %os.path.join(os.getcwd(),pharosPopupServerFileName))
	logger.info('Completed adding pharos popup server to login')
	
def installPrintQueuesUsingConfigFile():
	"""
	Installs print queues based on the printers.conf file
	"""
	logger.info('Installing print queues using config file %s' %printersConfigFile)
	config = ConfigParser.RawConfigParser()
	config.read(printersConfigFile)
	printersList = config.get('Printers','printers')
	logger.info('Printers list = %s' %printersList)
	printers = printersList.split(',')
	logger.info('Need to install total %d printers' %len(printers))
	for printer in printers:
		printer = printer.strip()
		logger.info('Installing printer %s' %printer)
		print('Installing printer %s' %printer)
		# Verfiy section
		if config.has_section(printer):
			logger.info('Printer %s is defined in config file' %printer)
			printerProperties = config.items(printer)			
			# convert to dictionary
			printerPropertiesDictionary = {'printqueue': printer}
			for pproperty in printerProperties:				
				printerPropertiesDictionary[pproperty[0]] = pproperty[1]			
			if (printerUtility.installPrintQueue(printerPropertiesDictionary)):
				logger.info('Successfully installed printer %s' %printer)
			else:
				logger.warn('Could not install printer %s as driver is missing' %printer)
		else:
			logger.error('Printer %s is not defined in config file. Cannot install it' %printer)
	
def setupLoggingDirectories():
	"""
	Setup the permissions for log folders
	"""
	logger.info('Creating log directories')
	
	# Delete old directories if they exist
	if os.path.exists(pharosLogDIR):
		logger.info('Old log directory %s found.' %pharosLogDIR)
		logger.info('Now trying to delete %s' %pharosLogDIR)
		try:			
			shutil.rmtree(pharosLogDIR)
			logger.info('Successfully removed old log directory %s' %pharosLogDIR)
		except OSError as (errCode, errMessage):
			logger.error('Error removing old log directory %s' %pharosLogDIR)
			logger.error('Error Code: %s, Error Message: %s' %(errCode, errMessage))
		
	if not os.path.exists(pharosLogDIR):
		logger.info('Creating autostart directory %s' %pharosLogDIR)
		os.makedirs(pharosLogDIR)			
	else:
		logger.info('Autostart directory %s already exists' %pharosLogDIR)
	
	# Setup permissions for all users
	logger.info('Changing permission for directory %s' %pharosLogDIR)
	try:
		chmod = subprocess.check_output(['chmod', '777', pharosLogDIR])
		logger.info('Successfully updated permissions for %s' %pharosLogDIR)
	except CalledProcessError as (errCode, errMessage):
		logger.error('Could not set permissions for %s' %pharosLogDIR)	
		logger.error('Error: %s Message: %s' %(errCode, errMessage))
	
	# create individual log files
	for lfile in programLogFiles:
		logger.info('Creating log file %s' %os.path.join(pharosLogDIR, lfile))
		lfilehandle = open(os.path.join(pharosLogDIR, lfile), 'w')
		lfilehandle.close()
		logger.info('file created successfully')
		try:
			chmod = subprocess.check_output(['chmod', '777', os.path.join(pharosLogDIR, lfile)])
			logger.info('successfully changed permissions for file %s' %os.path.join(pharosLogDIR, lfile))
		except CalledProcessError as (errCode, errMessage):
			logger.error('Could not set permissions for %s' %s.path.join(pharosLogDIR, lfile))	
			logger.error('Error: %s Message: %s' %(errCode, errMessage))
	
def installUninstaller():
	"""
	Setup the uninstaller
	"""
	logger.info('Copying the uinstaller files')
	uninstallerFilePath = os.path.join(os.getcwd(), uninstallFile)
	if os.path.exists(uninstallerFilePath):
		logger.info('Copying uninstaller file %s to %s' %(uninstallerFilePath, pharosUninstallerDIR))
		try:
			shutil.copyfile(uninstallerFilePath, os.path.join(pharosUninstallerDIR, uninstallFile))
			logger.info('Successfully copied uninstaller file to %s'  %pharosUninstallerDIR)
			
			# Set executable bit
			logger.info('Setting up permissions on uninstaller file %s' %os.path.join(pharosUninstallerDIR, uninstallFile))
			try:
				chmod = subprocess.check_output(['chmod', '755', os.path.join(pharosUninstallerDIR, uninstallFile)])
				logger.info('Successfully set up permissions on uninstaller file %s' %os.path.join(pharosUninstallerDIR, uninstallFile))
			except subprocess.CalledProcessError:
				logger.error('Could not set up permissions on uninstaller file %s' %os.path.join(pharosUninstallerDIR, uninstallFile))			
		except:
			logger.error('Could not copy uninstall file to %s' %pharosUninstallerDIR)
		
		# Copy the shared library files
		logger.info('Checking if directory %s exists' %uninstallerSharedLibraryDIR)
		if not os.path.exists(uninstallerSharedLibraryDIR):
			logger.info('Trying to create directroy %s' %uninstallerSharedLibraryDIR)
			try:
				os.makedirs(uninstallerSharedLibraryDIR)
				logger.info('Successfully created directory %s' %uninstallerSharedLibraryDIR)
			except:
				logger.error('Could not create directory %s' %uninstallerSharedLibraryDIR)
		
		if os.path.exists(uninstallerSharedLibraryDIR):
			logger.info('Trying to copy shared library files')
			for libraryFile in uninstallerSharedLibraryFiles:
				fullPath = os.path.join(os.getcwd(), libraryFile)
				if os.path.exists(fullPath):
					logger.info('Copying file %s to %s' %(fullPath, uninstallerSharedLibraryDIR))
					try:
						shutil.copyfile(fullPath, os.path.join(uninstallerSharedLibraryDIR, libraryFile))
						logger.info('Successfully copied file %s to %s' %(fullPath, uninstallerSharedLibraryDIR))
					except:
						logger.error('Could not copy file %s to %s' %(fullPath, uninstallerSharedLibraryDIR))
				else:
					logger.warn('Library file %s not found' %(fullPath))
	else:
		logger.warn('uninstaller file %s does not exists' %uninstallerFilePath)
	
def uninstallAndExit():
	"""
	In case of error uninstall and exit
	"""
	pharosUninstaller.uninstall()
	sys.exit(1)

def acceptEULA(eulaFile):
	"""
	Prompts the user to accept the EULA
	"""	
	logger.info('Showing user the end user license agreement from file %s' %eulaFile)
	eulafd = open(eulaFile, 'r')
	for line in eulafd:
		print(line)
	eulafd.close()
	
	userChoice = raw_input('\nDo you accept the EULA (y/n)?:   ')
	if userChoice in ['y', 'Y', 'yes', 'Yes', 'yEs', 'yeS', 'YEs', 'yES', 'YES']:
		logger.info('User accepted the EULA')
		return True
	else:
		logger.warn('User did not accept the EULA')
		return False

def checkDrivers():
	"""
	Checks if the system has all the drivers specified in the printers.conf file
	"""
	logger.info('Checking if all the drivers used in %s are installed on the system' %printersConfigFile)
	if os.path.exists(printersConfigFile):
		config = ConfigParser.RawConfigParser()
		config.read(printersConfigFile)
		printersList = config.get('Printers','printers')
		logger.info('Printers list = %s' %printersList)
		printers = printersList.split(',')
		logger.info('Checking drivers for total %d printers' %len(printers))
		driverStatus = {}
		for printer in printers:
			printer = printer.strip()
			driverStatus[printer] = False
			logger.info('Checking printer %s' %printer)			
			# Verfiy section
			if config.has_section(printer):
				logger.info('Printer %s is defined in config file' %printer)
				printerModel = config.get(printer, 'model')
				printerDriver = config.get(printer, 'driver')
				if printerUtility.isDriverInstalled(printerModel, printerDriver):
					logger.info('Driver <%s> is installed on the system ' %printerDriver)
					driverStatus[printer] = True
				else:
					logger.error('Driver <%s> is not installed on the system ' %printerDriver)				
			else:
				logger.error('Printer %s is not defined in config file. Cannot install it' %printer)
		# Evaluate Driver Status
		print('Driver Status:\t')
		for driver in driverStatus.keys():
			if driverStatus[driver]:
				print('Driver for printer %s is installed' %driver)
			else:
				print('Driver for printer %s is not installed\nIf you wish to continue printer %s will not be available' %(driver, driver))
				userChoice = raw_input('\nDo you wish to continue (y/n)?:   ')
				if userChoice in ['y', 'Y', 'yes', 'Yes', 'yEs', 'yeS', 'YEs', 'yES', 'YES']:
					logger.info('User chose to continue without driver %s' %driver)				
				else:
					print('Installation aborted because of missing driver for printer %s\nInstall the driver and then run setup again!' %driver)
					logger.warn('User chose to quit setup. Exiting')
					uninstallAndExit()		
	else:
		print('Printer Definition file %s does not exists. Exiting installation' %printersConfigFile)
		uninstallAndExit()		
	
def main():
	"""
	The main installer script
	"""
	logger.info('Beginning %s' %sys.argv[0])
	
	if os.path.exists(os.path.join(os.getcwd(), 'EULA')):
		logger.info('The EULA file exists. Will prompt user for accepting EULA')
		if not acceptEULA(os.path.join(os.getcwd(), 'EULA')):
			uninstallAndExit()
	
	# check prerequisites
	print('Checking for pre-requisites')	
	checkPreReqs()
	
	# Check if all drivers are available
	print('Checking for drivers')
	checkDrivers()
	
	# Install backend
	print('Installing backend')	
	installBackend()
	
	# Install popup server files
	print('Installing Popup server')	
	installPopupServer()
	
	# Setup Popup server to run at login
	print('Adding popup server to login')	
	addPopupServerToLogin()
	
	# Setup Log Directories
	print('Setting up log directories')	
	setupLoggingDirectories()
	
	# Setup Print Queues
	print('Installing printer queues')	
	installPrintQueuesUsingConfigFile()
	
	# Install Uninstaller
	print('Adding uninstaller')	
	installUninstaller()
	
	print('\nIIT Remote printing has been successfully installed on your computer. Please restart your GUI session to complete the installation process. The simplest way to do this is to log out and log back in!')

# Main Script ============================

# Create logger
logger = logging.getLogger('pharos-linux-setup')
logger.setLevel(logging.DEBUG)
# Create file handler
fh = logging.FileHandler(logFile)
fh.setLevel(logging.DEBUG)
# create console handler
ch = logging.StreamHandler()
ch.setLevel(logging.WARN)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
ch.setFormatter(formatter)
# add loggers
logger.addHandler(fh)
logger.addHandler(ch)

# import the pharosuninstall file
sys.path.append(os.getcwd())
try:	
	from printerutils import PrinterUtility
except:
	logger.error('Cannot import module printerutil')	
	sys.exit(1)

try:
	from processutils import ProcessUtility
except:
	logger.error('Cannot import module processutils')	
	sys.exit(1)
		
try:
	from pharosuninstall import PharosUninstaller
except:
	logger.error('Cannot import module pharosuninstall')	
	sys.exit(1)
	
# Create printer utility object
printerUtility = PrinterUtility(logger)
processUtils = ProcessUtility(logger)
pharosUninstaller = PharosUninstaller(logger, printerUtility, processUtils)

if __name__ == "__main__":
	main()
