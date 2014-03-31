#!/usr/bin/python2
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
pharosBackendFileName = 'pharos'
pharosPopupServerFileName = 'pharospopup'
pharosConfigFileName = 'pharos.conf'

popupServerInstallDIR = '/usr/local/bin'
pharosConfigInstallDIR = '/usr/local/etc'
pharosLogDIR = '/var/log/pharos'
programLogFiles = ['pharos.log', 'pharospopup.log']

# Functions =============================
class PharosUninstaller:
	"""
	Handles the uninstallation of the pharos remote printing package
	"""
	def __init__(self, log, printerUtil, processUtil):
		self.logger = log
		self.printerUtility = printerUtil
		self.processUtility = processUtil
		
	def uninstallPharosPrinters(self):
		"""
		Uninstall Pharos Printers
		"""
		self.logger.info('Uninstalling all pharos printers')
		allLocalPrinters = self.printerUtility.getAllPrinters()
		pharosPrinter = []
		for printer in allLocalPrinters.keys():
			printerSettings = allLocalPrinters[printer]
			if printerSettings.has_key('device-uri'):
				self.logger.info('Checking if printer %s with device uri %s is a pharos printer' %(printer, printerSettings['device-uri']))
				if re.match('pharos:\/\/', printerSettings['device-uri']):
					self.logger.info('Printer %s is a pharos printer' %printer)
					pharosPrinter.append(printer)
				else:
					self.logger.info('Printer %s is not a pharos printer' %printer)				
			else:
				self.logger.warn('could not find device-uri in printer settings %s' %printerSettings)
		
		allPharosPrintersDeleted = True
		if len(pharosPrinter) > 0:
			self.logger.info('There are total %s pharos printers installed on the system.' %len(pharosPrinter))			
			for printer in pharosPrinter:
				self.logger.info('Trying to delete printer %s' %printer)
				if self.printerUtility.deletePrinter(printer):
					self.logger.info('Printer %s successfully deleted' %printer)
				else:
					self.logger.info('Could not delete printer %s' %printer)
					allPharosPrintersDeleted = False			
		else:
			self.logger.warn('There are no pharos printers installed on the system')
		return allPharosPrintersDeleted
		
	def uninstallBackend(self):
		"""
		Uninstall Pharos Backend
		"""
		self.logger.info('Uninstalling pharos backend')
		backendDIR = '/usr/lib/cups/backend'
		backendFile = os.path.join(backendDIR, pharosBackendFileName)
		if os.path.exists(backendFile):
			self.logger.info('Backend file %s exists. Trying to remove it' %backendFile)
			try:
				os.remove(backendFile)
				logger.info('Successfully removed backend file: %s' %(backendFile))
			except:
				self.logger.info('Could not remove backend file %s' %backendFile)
		
		if os.path.exists(backendFile):
			self.logger.error('Could not remove backend file %s' %backendFile)
			return False
		else:
			return True
		
	def uninstallPharosPopupServer(self):
		"""
		Uninstall Pharos Popup Server
		"""
		self.logger.info('Uninstall Pharos Popup Server')
		
		# Kill popup server if running
		self.logger.info('Checking if popup server %s is running' %pharosPopupServerFileName)
		if self.processUtility.isProcessRunning(pharosPopupServerFileName):
			self.logger.info('Popup server is running. Trying to kill it')
			if self.processUtility.killProcess(pharosPopupServerFileName):
				self.logger.info('Popup server was successfully terminated')
			else:
				self.logger.error('Popup server could not be terminated. Popup server files will not be removed')
				return False		
		else:
			self.logger.info('Popup server is not running')
		
		# remove popup server files
		removedAllFiles = True
		self.logger.info('Checking for poup server executable')
		popupServerExecutable = os.path.join(popupServerInstallDIR, pharosPopupServerFileName)
		if os.path.exists(popupServerExecutable):
			self.logger.info('Poup server executable exists at %s. Trying to remove it.' %popupServerExecutable)
			try:
				os.unlink(popupServerExecutable)
				self.logger.info('Successfully removed popup server executable file %s' %popupServerExecutable)
			except:
				self.logger.error('Could not remove popup server executable file %s' %popupServerExecutable)
				removedAllFiles = False
		else:
			self.logger.warn('Popup server executable %s was already removed' %popupServerExecutable)
			
		# remove pharos config file
		self.logger.info('Checking for pharos config file')
		pharosConfigFilePath = os.path.join(pharosConfigInstallDIR, pharosConfigFileName)
		if os.path.exists(pharosConfigFilePath):
			self.logger.info('Pharos config file exists at %s. Trying to remove it.' %pharosConfigFilePath)
			try:
				os.unlink(pharosConfigFilePath)
				self.logger.info('Successfully removed pharos config file %s' %pharosConfigFilePath)
			except:
				self.logger.error('Could not remove pharos config file %s' %pharosConfigFilePath)
				removedAllFiles = False
		else:
			self.logger.warn('Pharos config file %s was already removed' %pharosConfigFilePath)
							
		return removedAllFiles
		
	def removePopupServerFromGnomeSession(self):
		"""
		Removes the popup server from GNOME session manager
		"""
		self.logger.info('Removing popup server from GNOME session manager')
		removedAllAutoStartFiles = True
		
		# Delete file from all users
		self.logger.info('Getting list of current users')
		currentUsers = os.listdir('/home')	
		for user in currentUsers:
			self.logger.info('Checking autostart file for user %s' %user)
			pharosAutoStartFile = os.path.join('/home', user, '.config', 'autostart', 'pharospopup.desktop')
			if os.path.exists(pharosAutoStartFile):
				self.logger.info('Autostart file %s found. Trying to delete it' %pharosAutoStartFile)
				try:
					os.unlink(pharosAutoStartFile)
					self.logger.info('Sucessfully removed file %s' %pharosAutoStartFile)
				except:
					self.logger.warn('Could not delete file %s' %pharosAutoStartFile)
					removedAllAutoStartFiles = False					
		
		# Delete file from root user
		rootAutoStartFile = os.path.join('/root', '.config', 'autostart', 'pharospopup.desktop')
		self.logger.info('Checking autostart file for root')
		if os.path.exists(rootAutoStartFile):
			self.logger.info('Trying to delete autostart file %s' %rootAutoStartFile)
			try:
				os.unlink(rootAutoStartFile)
				self.logger.info('Sucessfully removed file %s' %rootAutoStartFile)
			except:
				self.logger.warn('Could not delete file %s' %rootAutoStartFile)
				removedAllAutoStartFiles = False
		
		# Delete from future users
		skelAutoStartFile = os.path.join('/etc/', 'skel', '.config', 'autostart', 'pharospopup.desktop')
		self.logger.info('Checking autostart file for future users')
		if os.path.exists(skelAutoStartFile):
			self.logger.info('Trying to delete autostart file %s' %skelAutoStartFile)
			try:
				os.unlink(skelAutoStartFile)
				self.logger.info('Sucessfully removed file %s' %skelAutoStartFile)
			except:
				self.logger.warn('Could not delete file %s' %skelAutoStartFile)
				removedAllAutoStartFiles = False
			
		return removedAllAutoStartFiles
		
	def removePopupServerFromKDESession(self):
		"""
		Removes the popup server from KDE session manager
		"""
		self.logger.info('Removing popup server from KDE session manager')
		removedAllAutoStartFiles = True
		
		# Delete file from all users
		self.logger.info('Getting list of current users')
		currentUsers = os.listdir('/home')	
		for user in currentUsers:
			self.logger.info('Checking autostart file for user %s' %user)
			pharosAutoStartFile = os.path.join('/home', user, '.kde', 'Autostart', 'pharospopup')
			if os.path.exists(pharosAutoStartFile):
				self.logger.info('Autostart file %s found. Trying to delete it' %pharosAutoStartFile)
				try:
					os.unlink(pharosAutoStartFile)
					self.logger.info('Sucessfully removed file %s' %pharosAutoStartFile)
				except:
					self.logger.warn('Could not delete file %s' %pharosAutoStartFile)
					removedAllAutoStartFiles = False					
		
		# Delete file from root user
		rootAutoStartFile = os.path.join('/root', '.kde', 'Autostart', 'pharospopup')
		self.logger.info('Checking autostart file for root')
		if os.path.exists(rootAutoStartFile):
			self.logger.info('Trying to delete autostart file %s' %rootAutoStartFile)
			try:
				os.unlink(rootAutoStartFile)
				self.logger.info('Sucessfully removed file %s' %rootAutoStartFile)
			except:
				self.logger.warn('Could not delete file %s' %rootAutoStartFile)
				removedAllAutoStartFiles = False
		
		# Delete from future users
		skelAutoStartFile = os.path.join('/etc/skel', '.kde', 'Autostart', 'pharospopup')
		self.logger.info('Checking autostart file for future users')
		if os.path.exists(skelAutoStartFile):
			self.logger.info('Trying to delete autostart file %s' %skelAutoStartFile)
			try:
				os.unlink(skelAutoStartFile)
				self.logger.info('Sucessfully removed file %s' %skelAutoStartFile)
			except:
				self.logger.warn('Could not delete file %s' %skelAutoStartFile)
				removedAllAutoStartFiles = False
			
		return removedAllAutoStartFiles		
			
	def uninstallStartupEntries(self):
		"""
		Uninstalls the startup entries from the session manager
		"""
		self.logger.info('Removing Session Manager Startup entries for pharos poups')
		self.logger.info('Analyzing desktop environment')
		returnCode = False
		if self.processUtility.isProcessRunning('gnome'):
			self.logger.info('User is using gnome window manager')
			if self.removePopupServerFromGnomeSession():
				self.logger.info('Successfully cleaned up startup entries from GNOME session')
				returnCode = True
			else:
				self.logger.warn('Could not remove all startup entries from GNOME session')
				returnCode = False
		elif self.processUtility.isProcessRunning('kde'):
			self.logger.info('User is using kde Window Manager')
			if self.removePopupServerFromKDESession():
				self.logger.info('Successfully cleaned up startup entries from KDE session')
				returnCode = True
			else:
				self.logger.warn('Could not remove all startup entries from KDE session')
				returnCode = False
		else:
			self.logger.warn('Users window manager is not recognized. Could not remove login scripts for popupserver. Please use your window manager to remove startup script %s' %os.path.join(popupServerInstallDIR,pharosPopupServerFileName))
		self.logger.info('Completed removing pharos popup server from login')
		return returnCode
		
	def uninstallLogFiles(self):
		"""
		Remove log files used
		"""
		self.logger.info('Uninstall Log Files')
		self.logger.info('Checking if log directory exists at %s' %pharosLogDIR)
		if os.path.exists(pharosLogDIR):
			self.logger.info('Log directory exists. Trying to remove it')
			try:
				shutil.rmtree(pharosLogDIR)
				self.logger.info('Successfully removed directory %s' %pharosLogDIR)
			except:
				self.logger.error('Could not remove directory %s' %pharosLogDIR)
				return False
		
		return True		

	def uninstall(self):
		""""
		The main function
		"""
		self.logger.info('Beginning pharos uninstallation')
		returnCode = True
		print('Uninstalling all pharos printers')
		if (self.uninstallPharosPrinters()):
			self.logger.info('All pharos printers have been deleted. Can proceed with uninstalling the CUPS pharos backend')
			if self.uninstallBackend():
				self.logger.info('Successfully removed backend file')
			else:
				self.logger.error('Could not remove backend file')
				returnCode = False
		else:
			self.logger.warn('All pharos printers could not be deleted. Will not be removing the CUPS pharos backend')
		
		print('Uninstalling pharos popup server')
		if self.uninstallPharosPopupServer():
			self.logger.info('Successfully removed pharos popup file')
		else:
			self.logger.error('Could not remove pharos popup file')
			returnCode = False
		
		print('Uninstalling autostart entries from GUI session manager')
		if self.uninstallStartupEntries():
			self.logger.info('Successfully removed startup entries for pharos popup')
		else:
			self.logger.error('Could not remove startup entries for pharos popup')
			returnCode = False
		
		print('Uninstalling log files')
		if self.uninstallLogFiles():
			self.logger.info('Successfully removed pharos log files')
		else:
			self.logger.error('Could not remove startup pharos log files')
			returnCode = False
		return returnCode
