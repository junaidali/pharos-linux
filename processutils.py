#!/usr/bin/python
# Script Name: processutils.py
# Script Function:
#	This script provides utility functions for dealing with processes
#
# Author: Junaid Ali
# Version: 1.0

__name__ = 'processutils'
__version__ = '1.0'

# Imports ===============================

import subprocess
import re
import os
import signal
import time

# Class definitions =====================
class ProcessUtility:
	def __init__(self, log):
		"""
		Constructor
		"""
		self.logger = log
	
	def isProcessRunning(self, processName):
		"""
		Checks if the given process is running
		"""
		self.logger.info('Checking if %s is running' %processName)
		self.logger.info('Getting list of processes')
		try:
			ps = subprocess.check_output(['ps', 'ax'])
		except CalledProcessError as (errCode, errMessage):
			self.logger.error('Could not get list of running processes')
			self.logger.error('Error: %s Message: %s' %(errCode, errMessage))
			return False
			
		processes = ps.split('\n')
		processFound = False
		for process in processes:
			if re.search(processName, process):
				self.logger.info('%s is running with details: %s ' %(processName, process))
				processFound = True
				break			
		if processFound:
			self.logger.info('%s is running.' %processName)
			return True
		else:
			self.logger.info('%s is not running.' %processName)
			return False
		
	def killProcess(self, processName):
		"""
		kills a running process with given name
		"""
		self.logger.info('Trying to kill %s' %processName)
		process = subprocess.Popen(["pgrep", processName], stdout=subprocess.PIPE)
		for pid in process.stdout:
			self.logger.info('Trying to kill process with PID %s' %pid)
			os.kill(int(pid), signal.SIGTERM)			
			self.logger.info('Waiting for 5 seconds after sending Terminate signal to process PID %s' %pid)
			# Sleep for 5 seconds
			time.sleep(5)
			
		if self.isProcessRunning(processName):
			self.logger.warn('Process %s could not be killed' %processName)
			return False
		else:
			self.logger.info('Successfully killed process %s' %processName)
			return True
