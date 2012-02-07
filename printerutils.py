
import subprocess
import re

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
