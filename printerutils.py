#!/usr/bin/python
# Script Name: printerutils.py
# Script Function:
#	This script provides utility functions for dealing with print queues
#
# Author: Junaid Ali
# Version: 1.0

__name__ = 'printerutil'
__version__ = '1.0'

# Imports ===============================

import subprocess
import re
import tempfile
import os
import shutil
import stat

# Class definitions =====================
class PrinterUtility:
	def __init__(self, log):
		self.logger = log
	
	def printerExists(self, printer):
		"""
		Checks if the given printer device exists
		"""
		self.logger.info('Deleting printer')
		self.logger.info('Checking if printer %s exists' %printer)
		printerExistsCommand = ['lpoptions', '-d', printer]
		
		self.logger.info('Checking if printer %s already exists using command %s' %(printer, printerExistsCommand))
		try:
			printerExistsCommandResult = subprocess.check_output(printerExistsCommand,stderr=subprocess.STDOUT)
			self.logger.info('Result of printer delete command %s' %printerExistsCommandResult)
			if re.search('Unknown printer or class', printerExistsCommandResult):
				self.logger.info('Printer %s does not exists' %printer)
				return False
			else:
				self.logger.info('Printer %s already exists' %printer)
				return True
		except subprocess.CalledProcessError:
			self.logger.warn('Could not check if printer exists using lpoptions command')		
			
		return False
	
	def deletePrinter(self, printer):
		"""
		Deletes the given printer device
		"""
		self.logger.info('Trying to delete printer device %s' %printer)
		deletePrinterCommand = ['lpadmin', '-x', printer]
		self.logger.info('Trying to delete printer %s using command %s' %(printer, deletePrinterCommand))
		try:
			deletePrinterCommandResult = subprocess.call(deletePrinterCommand)		
		except subprocess.CalledProcessError:
			self.logger.error('Could not delete printer %s using lpadmin command' %printer)	 	
			return False
		
		# check if printer still exists
		if not self.printerExists(printer):
			return True
		else:
			return False		

	def enablePrinter(self, printer):
		"""
		Enables printer device
		"""
		
		acceptPrinterCommand = ['cupsaccept', printer]
		self.logger.info('Trying to enable printer %s using command %s' %(printer, acceptPrinterCommand))
		try:
			acceptPrintCommandResult = subprocess.call(acceptPrinterCommand)
			self.logger.info('Result = %s' %acceptPrintCommandResult)
		except subprocess.CalledProcessError:
			self.logger.error('Could not accept printer %s using cupsaccept command' %printer)	 	
			return False
		
		enablePrinterCommand = ['cupsenable', printer]
		self.logger.info('Trying to enable printer %s using command %s' %(printer, enablePrinterCommand))
		try:
			enablePrintCommandResult = subprocess.call(enablePrinterCommand)
			self.logger.info('Result = %s' %enablePrintCommandResult)
		except subprocess.CalledProcessError:
			self.logger.error('Could not enable printer %s using cupsenable command' %printer)	 	
			return False
		
		return True
	
	def installPrintQueue(self, printer):
		"""
		Install a print queue	
		"""
		self.logger.info('Installing printer %s' %printer)
		
		# check if all required parameters are present
		if printer['driver'] == None or printer['model'] == None or printer['lpdserver'] == None or  printer['lpdqueue'] == None:
			self.logger.error('One of the required parameters (driver, model, lpdserver, lpdqueue) is missing. Cannot add printer')
			return False		
		
		# Check if driver is specified
		if printer['driver'] != None:
			self.logger.info('Printer driver <%s> is defined' %printer['driver'])
			self.logger.info('Fixing Printer driver name')
			if re.search('\(|\)', printer['driver']):
				self.logger.info('Printer Driver name <%s> contains brackets' %printer['driver'])
				printer['driver'] = re.sub('\(', '\(', printer['driver'])
				printer['driver'] = re.sub('\)', '\)', printer['driver'])
				self.logger.info('Printer driver after fixing brackets: %s' %printer['driver'])
		
		# Query for driver using make and model
		printerDriverPath = ''
		driverFound = False		
		if printer['model'] != None:
			self.logger.info('Printer model <%s> is defined. Now searching for driver' %printer['model'])
			try:
				lpinfo = subprocess.check_output(['lpinfo', '--make-and-model',printer['model'], '-m'])			
			except subprocess.CalledProcessError:
				self.logger.error('Could not get printer driver details using lpinfo')		
				return False			
			# Process results of lpinfo
			driversList = lpinfo.split('\n')
			self.logger.info('Total %d drivers returned for <%s> make and model' %(len(driversList), printer['model']))		
			for driver in driversList:
				driverPath = driver.split(' ')[0]
				driverName = driver.lstrip(driverPath)
				# remove white spaces if any
				driverPath = driverPath.strip()
				driverName = driverName.strip()
				if driverName != '':
					self.logger.info('checking if driver <%s> matches <%s>' %(driverName, printer['driver']))
					if re.search(printer['driver'], driverName):
						self.logger.info('Driver matches')
						driverFound = True
						printerDriverPath = driverPath
						break
					else:
						self.logger.warn('Driver does not match')
		
		if driverFound:
			# Check if printer already exists.
			if self.printerExists(printer['printqueue']):
				if self.deletePrinter(printer['printqueue']):
					self.logger.info('Printer %s successfully deleted' %printer['printqueue'])
				else:
					self.logger.error('Printer %s could not be deleted' %printer['printqueue'])
					self.logger.error('Will not try to add the printer again')
					return False
					
			self.logger.info('Using driver path %s' %printerDriverPath)
			# Build lpadmin Command
			deviceURI = 'pharos://' + printer['lpdserver'] + '/' + printer['lpdqueue']
			lpadminCommand = ['lpadmin', '-E', '-p', printer['printqueue'] , '-v', deviceURI, '-m', printerDriverPath]
			if printer['location'] != None:
				lpadminCommand.append('-L')
				lpadminCommand.append(printer['location'])
			if printer['description'] != None:
				lpadminCommand.append('-D')
				lpadminCommand.append(printer['description'])			
			
			# Run lpadmin command
			try:
				self.logger.info('Adding printer using lpadmin command: %s' %lpadminCommand)
				lpadmin = subprocess.check_output(lpadminCommand)
				self.logger.info('command result = %s' %lpadmin)
			except subprocess.CalledProcessError:
				self.logger.error('Could not add printer using lpadmin')
			
			# Enable Duplex if needed
			if printer.has_key('duplex'):
				if printer['duplex'] == 'yes' or printer['duplex'] == 'Yes' or printer['duplex'] == 'YES':
					self.logger.info('Enabling duplex printing for printer %s' %printer['printqueue'])
					
					if printer.has_key('make'):
						if printer['make'] == 'hp' or printer['make'] == 'HP' or printer['make'] == 'Hp' or printer['make'] == 'hP':
							self.logger.info('Processing duplex printing for HP printer')
							if self.enableDuplexPrintingForHPPrinter(printer['printqueue']):
								self.logger.info('Successfully enabled duplexing for printer %s' %printer['printqueue'])
							else:
								self.logger.warn('Could not enable duplexing for printer %s' %printer['printqueue'])
						
					if self.enableDuplexPrinting(printer['printqueue']):
						self.logger.info('Successfully enabled duplexing for printer %s' %printer['printqueue'])
					else:
						self.logger.warn('Could not enable duplexing for printer %s' %printer['printqueue'])
				else:
					self.logger.info('No need to enable duplexer for printer %s' %printer['printqueue'])
							
			# Enable Printer
			if self.enablePrinter(printer['printqueue']):
				self.logger.info('Successfully enabled printer %s' %printer['printqueue'])
			else:
				self.logger.warn('Could not enable printer %s' %printer['printqueue'])		
			
			if self.printerExists(printer['printqueue']):
				self.logger.info('Successfully created printer %s' %printer['printqueue'])
				return True
			else:
				self.logger.error('Could not create printer %s' %printer['printqueue'])
				return False		
			
		else:
			self.logger.error('Could not find the required driver installed on the system. Cannot install printer')
			return False		

	
	def queryPrinterOption(self, printer, option):
		"""
		Queries the printer for a specific option
		"""
		queryCommand = ['lpoptions', '-p', printer]
		value = ''
		self.logger.info('Querying printer for option %s' %option)
		try:
			lpoption = subprocess.check_output(queryCommand)
			allOptions = lpoption.split(' ')
			allOptionsDictionary = {}
			for pOption in allOptions:
				if re.search('=', pOption):
					allOptionsDictionary[pOption.split('=')[0].strip()] = pOption.split('=')[1].strip()
			
			if allOptionsDictionary.has_key(option):
				value = allOptionsDictionary[option]
				
		except subprocess.CalledProcessError:
			self.logger.error('Could not set option %s with value %s printer %s' %(option, value, printer))			
		
		if value != '':
			self.logger.info('The printer has option %s set to %s' %(option, value))
		return value
	
	def setPrinterOption(self, printer, option, value):
		"""
		Sets a given option for the printer device
		"""
		self.logger.info('Setting option %s with value %s for printer %s' %(option, value, printer))
		optionString = option + "=" + value
		printerOptionCommand = ['lpoptions', '-p', printer, '-o', optionString]
		self.logger.info('Running lptions command %s' %printerOptionCommand)
		try:
			lpoption = subprocess.check_output(printerOptionCommand)
		except subprocess.CalledProcessError:
			self.logger.error('Could not set option %s with value %s printer %s' %(option, value, printer))		
			return False
		
		self.logger.info('Checking if option was correctly set')
		currentValue = self.queryPrinterOption(printer, option)
		if currentValue == value:
			self.logger.info('The option %s has been correctly setup to %s for printer %s' %(option, value, printer))
		else:
			self.logger.warn('The option %s has been incorrectly setup to %s for printer %s' %(option, currentValue, printer))
	
	def enableDuplexPrintingForHPPrinter(self, printer):
		"""
		Enables duplexing for HP printer
		"""
		self.logger.info('Enabling duplex printing for HP printer %s' %printer)
		
		# Update the driver ppd
		ppdFile = os.path.join('/etc/cups/ppd', printer + '.ppd')
		newppdFile = tempfile.NamedTemporaryFile(delete=False)
		
		self.logger.info('Checking if ppd file %s exists' %ppdFile)
		if os.path.exists(ppdFile):
			self.logger.info('ppd file %s exists' %ppdFile)
			ppd = open(ppdFile, 'r')
			for line in ppd:				
				if line.startswith("*DefaultDuplex: None", 0, len("*DefaultDuplex: None")):
					newppdFile.writelines('*DefaultDuplex: DuplexNoTumble\n')
				elif line.startswith("*DefaultOptionDuplex: False", 0, len("*DefaultOptionDuplex: False")):
					newppdFile.writelines('*DefaultOptionDuplex: True\n')
				else:
					newppdFile.writelines(line)
			newppdFile.close()
			ppd.close()
			self.logger.info('successfully created file %s' %newppdFile.name)
			try:				
				shutil.copy(newppdFile.name, ppdFile)
				self.logger.info('Successfully copied the modified ppd file to %s' %ppdFile)
				
				# update permission on new file
				if os.path.exists(ppdFile):
					self.logger.info('Updating permissions on file %s' %ppdFile)
					try:
						chmod = subprocess.call(['chmod', '644', ppdFile])
					except subprocess.CalledProcessError:
						self.logger.error('Could not change permission for file %s' %ppdFile)						
					
				# delete temp file
				os.remove(newppdFile.name)
				self.logger.info('Successfully deleted file %s' %newppdFile)
			except IOError as (errCode, errMessage):
				logger.error('Could not copy file %s to %s' %(newppdFile.name, ppdFile))	
				logger.error('Error: %s Message: %s' %(errCode, errMessage))			
		else:
			self.logger.warn('ppd file %s does not exists' %ppdFile)
		
		self.logger.info('Successfully enabled duplexing for printer %s' %printer)
		return True
			
	def enableDuplexPrinting(self, printer):
		"""
		Enables default duplex printing
		"""
		self.logger.info('Enabling duplex printing for printer %s' %printer)
		
		enableDuplexCommand = ['lpoptions', '-p', printer, '-o', 'duplex=DuplexNoTumble']
		self.logger.info('Enabling duplex printing for printer %s using command %s' %(printer, enableDuplexCommand))
		try:
			lpinfo = subprocess.check_output(enableDuplexCommand)
		except subprocess.CalledProcessError:
			self.logger.error('Could not enable duplexing for printer %s' %printer)		
			return False
		
		self.logger.info('Successfully enabled duplexing for printer %s' %printer)
		return True
			
	def getAllPrintersByBackend(self, backend=None):
		"""
		returns all printers by queue backend
		e.g. lpd, usb, socket, etc.
		"""
		self.logger.info('Getting list of all printers by queue backend type')
		queryPrinterCommand = ['lpstat', '-p']
		self.logger.info('Querying printers using')
