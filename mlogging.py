#
# Logging wrapper.
#
# Author: Andreas Kraft (akr@mheg.org)
#
# DISCLAIMER
# You are free to use this code in any way you like, subject to the
# Python disclaimers & copyrights. I make no representations about the
# suitability of this software for any purpose. It is provided "AS-IS"
# without warranty of any kind, either express or implied. So there.
#
"""	Wrapper class for the logging subsystem. """


import	logging, logging.handlers, time

class	Logging:
	""" Wrapper class for the logging subsystem. This class wraps the 
		initialization of the logging subsystem and provides convenience 
		methods for printing log, error and warning messages to a 
		logfile and to the console.
	"""
	# some logging defaults
	_logFile	= 'log.log'
	_logSize	= 1000000
	_logCount	= 10
	_logLevel	= logging.INFO
	_isinit		= False


	def __init__(self, logFile = _logFile, logSize = _logSize, logCount = _logCount, logLevel = _logLevel):
		"""Init the logging system.
		"""

		if self._isinit == True:	return
				
		self.logger			= logging.getLogger('logging')
		logfp				= logging.handlers.RotatingFileHandler(logFile, maxBytes=logSize, backupCount=logCount)
		logformatter		= logging.Formatter('%(asctime)s %(levelname)s %(message)s')
		logfp.setFormatter(logformatter)
		self.logger.addHandler(logfp) 
		self.logLevel = logLevel
		logfp.setLevel(logLevel)
		self.logger.setLevel(logLevel)
		self._isinit = True
	

	def log(self, msg):
		"""Print a log message with level INFO.
		"""
		
		try:
			if self.logLevel <= logging.INFO:
				print( "(" + time.ctime(time.time()) + ") " + msg)
				if self._isinit:
					self.logger.info(msg) 
		except:
			pass


	def logdebug(self, msg):
		"""Print a log message with level DEBUG.
		"""
		
		try:
			if self.logLevel <= logging.DEBUG:
				print("DEBUG: (" + time.ctime(time.time()) + ") " + msg)
				if self._isinit:
					self.logger.debug(msg) 
		except:
			pass


	def logerr(self, msg):
		"""Print a log message with level ERROR.
		"""
		
		try:
			if self.logLevel <= logging.ERROR:
				print("ERROR: (" + time.ctime(time.time()) + ") " + msg)
				if self._isinit:
					self.logger.error(msg) 
		except:
			pass
	
	def logwarn(self, msg):
		"""Print a log message with level WARNING.
		"""
		
		try:
			if self.logLevel <= logging.WARNING:
				print("Warning: (" + time.ctime(time.time()) + ") " + msg)
				if self._isinit:
					self.logger.warning(msg) 
		except:
			pass
