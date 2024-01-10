#
# smtpproxy.py
# Version 1.5
#
# Author: Andreas Kraft (akr@mheg.org)
#
# DISCLAIMER
# You are free to use this code in any way you like, subject to the
# Python disclaimers & copyrights. I make no representations about the
# suitability of this software for any purpose. It is provided "AS-IS"
# without warranty of any kind, either express or implied. So there.
#
#
#	TODO
#	make removing of files in case of an error configuratble
#	Document handlers
#	Mail handlers: specify the order of the handlers to be called
#	Mail handlers: handle the returned and possible modified email
#	Implement SMTP authenticiation
#
"""smtpproxy.py - A Python SMTP Proxy Server.

This Python module implements a proxying SMTP server. It can be used to forward
mail through different "real" SMTP servers, depending on the sender. The main
purpose of the server, however, is to enable applications that do not support
the POP-before-SMTP authentication scheme of some SMTP server.

The server stores mails temporarly in a directory. A separate thread is then
responsible to send the mails to the configurated destination SMTP server,
optionally performing the POP-before-SMTP authentication.

The proxy server is configured by an ini-style configuration file in the
current working directory of the server. It consists of the following sections:

The basic configuration of the server.

	[config]
	port=<int>           : The port to listen on. Optional. The default is 25.
	sleeptime=<int>      : The time to wait for the relaying thread to wait between checks, in seconds. Optional. The default is 30.
	debuglevel=<int>     : Set the debuglevel for various functions. The default is 0 (no debug output).
	waitafterpop=<int>   : The time to wait after pop authentication.
	deleteonerror=<bool> : Delete a mail when an error occurs

The configuration of the logging sub-system.

	[logging]
	file=<str>           : Path and name of the log file. Optional. The default is 'smtpproxy.log'.
	size=<int>           : Size of the logfile before splitting it up into a new logfile. Optional. The default is 1000000.
	count=<int>          : Number of logfiles to keep. Optional. The default is 10.
	level=<str>          : One of DEBUG, INFO, WARNING, ERROR or NONE. In case of NONE, only critical errors are logged. Optional. The default is INFO.

The configuration for the sender's mail accounts. This section can be appear more
than once in the configuration file. Actually, for each sender's mail account
one section must be configured.

	[<mail address of the sender, eg. foo@bar.com>]
	smtphost=<str>       : The host name of the receiving SMTP server. Mandatory.
	smtpport=<int>       : The port of the receiving SMTP server. Optional. The default is depends on the smtpsecurity type (25 or 465).
	smtpsecurity=<str>   : Indicates the type of the communication security to the SMTP server. Either "tls", "ssl", or "none" (all lowercase). The default is "none".
	popbeforesmtp=<bool> : Indicates whether POP-before-SMTP authentication must be performed. Optional. The default is false.
	pophost=<str>        : The host name of the POP3 server. Mandatory only if popbeforesmtp is set to true.
	popport=<int>        : The port of the POP3 server. Optional. The default is 995.
	popssl=<bool>		 : Indicates whether the POP connection should be using SSL. The default is true.
	popusername=<str>    : The username for the POP3 account. Mandatory only if popbeforesmtp is set to true.
	poppassword=<str>    : The password for the POP3 account. Mandatory only if popbeforesmtp is set to true.
	popcheckdelay=<int>  : The time to wait before it is needed to reauthenticate again with the POP3 server, in seconds. Optional. The default is 60.
	smtpusername=<str>   : The username for the SMTP account. This must be provided if the SMTP server needs authentication.
	smtppassword=<str>   : The password for the SMTP account. This must be provided if the SMTP server needs authentication.
	localhostname=<str>  : The hostname used by the proxy to identify the host it is running on to the remote SMTP server. Optional.

	returnpath=<str>     : Specifies a bounce email address for a message. Optional.
	replyto=<str>        : Specifies a reply email address for a message response. Optional.

	use=<str>            : The name of another account configuration. If this is set then the configuration data of that account is taken instead.


"""

import logging, os, pickle, sys, time, email, types, tempfile
import config, mlogging, smtps
if sys.version_info[0] > 2:
    from _thread import *
else:
    from thread import *
from base64 import b64encode
from inspect import getmembers, isfunction, isclass



class MailAccount:
	""" This class holds the attributes of a mail account. It acts as a container
		for the following variables and is usually filled by the data
		read from the configuration file.

		* rsmtphost - The SMTP server host. The default is None.
		* rsmtpport - The SMTP server port. The default is 25.
		* rsmtpsecurity - Use tls, ssl or none security for the connection to the SMTP server. The default is none.
		* rpophost - The POP server host. The default is None.
		* rpopport - The POP server port. The default is 995.
		* rpopssl - Use SSL for the POP3 connection. The default is True.
		* rpopuser - The POP user name. The default is None.
		* rpoppass - The POP password. The default is None.
		* rsmtpuser - The SMTP user name. The default is None.
		* rsmtppass - The SMTP password. The default is None.
		* rPBS - Perform pop-before-smtp authentication. The default is false.
		* rpopcheckdelay -  The time before a new POP-before-SMTP authentication is performed. The default is 60 second.
		* localhostname - The local hostname the proxy uses to authenticate itself to the remote SMTP server. The default is None.
		* returnpath - Specifies a bounce email address for a message. The default is None.
		* replyto - Specifies a reply email address for a message response. The default is None.
		* useconfig - The name of another account configuration. If this is set then the configuration data of that account is taken instead.
	"""

	def __init__(self):
		"""Initialize instance variables."""
		self.rsmtphost			= None
		self.rsmtpport			= 0
		self.rsmtpsecurity		= 'none'
		self.rpophost			= None
		self.rpopport			= 995
		self.rpopssl			= True
		self.rpopuser			= None
		self.rpoppass			= None
		self.rsmtpuser			= None
		self.rsmtppass			= None
		self.rPBS				= False
		self.rpopcheckdelay		= 60	# in sec
		self.localhostname		= None
		self.returnpath			= None
		self.replyto			= None
		self.useconfig			= None



class Mail:
	""" This calss holds a received e-mail. It holds all the necessary
		attributes of a mail. Istances of this class are written temporarly to
		the filesystem and scheduled for later sending.
	"""

	def __init__(self):
		""" Initialize intstance variables."""
		self.msg	= None
		self.to		= []
		self.frm	= ''


# Internal variables
receivedHeader		= 'Python SMTP Proxy'	# The identifier of the SMTP proxy server that is inserted in the e-mail header.
smtpconfig			= None
mailaccounts		= {}
configFile 			= 'smtpproxy.ini'
port				= 25
msgdir				= ''
sleeptime			= 30
waitafterpop		= 5
popchecktime		= 0
debuglevel			= 0
deleteonerror		= True

# Mail handler
mailHandlerDir = os.path.dirname(os.path.abspath(__file__)) + '/handlers'
mailHandlers = {}

# logging defaults
logFile		= 'smtpproxy.log'
logSize		= 1000000
logCount	= 10
logLevel	= logging.INFO


class SMTPProxyService(smtps.SMTPServerInterface):
	"""	This class is initiated every time a connection to the SMTP server is
		established. It handles the receiving of one e-mail. After receiving
		the mail, it is stored in the local file system and scheduled for
		forwarding.
	"""

	def __init__(self):
		"""	Initialize the instance.
		"""
		self.mail = Mail()


	def mailFrom(self, args):
		"""	Receive the from: part (sender) of the e-mail.
		"""

		# Stash who its from for later
		self.mail.frm = smtps.stripAddress(args)


	def rcptTo(self, args):
		"""	Receive the to; part (receipient) of the e-mail.
		"""

		# Stashes multiple RCPT TO: addresses
		self.mail.to.append(args.split(":")[1].strip())


	def data(self, args):
		""" Receive the remeining part of the e-mail (beside of the from: and
			to: received earlier, ie. the remaining header and the body part
			of the e-mail).
			A new received: header is added to the header.
			An optional return-path: header is added to the header.
			An optional reply-to: header is added to the header.
			Finally, the e-mail is stored in the file system.
		"""

		import email.Utils
		global	msgdir, receivedHeader

		self.mail.msg = ( args )

		# call the mail handlers to process this message
		# TODO: specify the order of the handlers to be called
		# TODO: handle the returned and possible modified email
		try:
			msg = email.message_from_string(self.mail.msg)
			for h in mailHandlers:
				# Call all mail handlers. If any of the mail handlers
				# returns False then the mail is not further processed and
				# discarded.
				if not mailHandlers[h].handleMessage(msg, self.mail, self):
					mlog.log('MailHandler "' + mailHandlers[h].__class__.__name__ + '" canceled processing. Mail discarded.')
					return
		except:
			mlog.logerr('Message handler caught exception: ' +  str(sys.exc_info()[0]) +": " + str(sys.exc_info()[1]))

		# Get account data

		account = getMailAccount(self.mail.frm)
		if account == None:
			mlog.logerr('No account data found for ' + self.mail.frm)
			return


		# Add headers at the start!
		self.mail.msg = 'Received: (' + receivedHeader + ') ' + email.Utils.formatdate() + '\n' + self.mail.msg
		#self.mail.msg = ("From: %s\r\nTo: %s\r\n%s" % (self.mail.frm, ", ".join(self.mail.to), args))
		if account.returnpath != None:
			self.mail.msg = 'Return-Path: ' + account.returnpath + '\n' + self.mail.msg
		if account.replyto != None:
			self.mail.msg = 'Reply-To: ' + account.replyto + '\n' + self.mail.msg

		# Save message
		try:
			(file, fn) = tempfile.mkstemp(suffix='.msg', dir=msgdir)
			pickle.dump(self.mail, os.fdopen(file, 'w'))
		except:
			mlog.logerr('Saving mail caught exception: ' +  str(sys.exc_info()[0]) +": " + str(sys.exc_info()[1]))
			return
		mlog.log('Mail scheduled for sending (' + fn + ')')



	def setTo(self, newTo):
		""" Callback for changing the to: field of a message.
		"""
		msg = email.message_from_string(self.mail.msg)
		msg.replace_header('To', newTo)
		self.mail.to = [ newTo ]
		self.mail.msg =  str(msg)


	def setFrom(self, newFrom):
		""" Callback for changing the from: field of a message.
		"""
		self.mail.frm = newFrom
		# TODO



def	sendMail(mail, filename = None):
	""" Send an e-mail to a real SMTP server, depending on the sender's
		configuration. First, the configuration is checked, then (if
		necessary), a POP-before-SMTP authentication is performed before
		actually sending the mail.
	"""

	import poplib, smtplib
	global popchecktime, mailaccounts, waitafterpop, debuglevel

	# find mail configuration for the sender's mail account
	account = getMailAccount(mail.frm)
	if account == None:
		mlog.logerr('No account data found for ' + mail.frm + ' (' + filename + ')')
		return False

	# First do POP-Before-SMTP, if necessary
	if account.rPBS and (popchecktime + account.rpopcheckdelay) < time.time():
		try:
			mlog.log("Performing Pop-before-SMTP")

			M = poplib.POP3_SSL(account.rpophost, account.rpopport)
			M.user(account.rpopuser)
			M.pass_(account.rpoppass)
			M.quit()

			popchecktime = time.time()

			time.sleep(waitafterpop)
		except:
			mlog.logerr('POP-before-SMTP caught exception: ' +  str(sys.exc_info()[0]) +": " + str(sys.exc_info()[1]))
			return False

	# Send mail
	try:
		mlog.log("Sending mail from: " + mail.frm + " to: " + ",".join(mail.to))
		mlog.logdebug("Port: " + str(account.rsmtpport))

		smtpFunc = smtplib.SMTP
		if account.rsmtpsecurity == 'ssl':
			smtpFunc = smtplib.SMTP_SSL
			mlog.log("Using SSL")

		if account.localhostname != None:
			server = smtpFunc(account.rsmtphost, account.rsmtpport, account.localhostname)
		else:
			server = smtpFunc(account.rsmtphost, account.rsmtpport)
		server.set_debuglevel(debuglevel)
		server.ehlo()
		if account.rsmtpsecurity == 'tls':
			mlog.log("Using TLS")
			server.starttls()
			server.ehlo()
		if account.rsmtpuser != None:
			try:
				server.login(account.rsmtpuser, account.rsmtppass)
			except smtplib.SMTPAuthenticationError:
				# There is a problem with the python smtplib: the login() method doesn't try
				# the other authentication methods, even when the server tell to do so.
				# So we have to try it for ourselves.
				# For now, only the PLAIN authentication method is tried.
				(code, resp) = server.docmd("AUTH", "PLAIN " + encode_plain(account.rsmtpuser, account.rsmtppass))
				mlog.log("authentication. Code = " + str(code) + ", response = " + resp)
				if code == 535:
					mlog.logerr('Authentication error')
		server.sendmail(mail.frm, mail.to, mail.msg)
		server.quit()
	except:
		# TODO: check Greylist errror
		mlog.logerr('SMTP caught exception: ' +  str(sys.exc_info()[0]) +": " + str(sys.exc_info()[1]))
		return False
	return True


def encode_plain(user, password):
	""" Encode a user name and password as base64.
	"""
	return b64encode("\0%s\0%s" % (user, password))


def getMailAccount(frm):
	""" Find and return the mail account data for a from: address, or None.
	"""
	account = None
	if frm in mailaccounts.keys():
		account = mailaccounts[frm]
		if account.useconfig != None:
			if account.useconfig in mailaccounts.keys():
				account = mailaccounts[account.useconfig]
			else:
				mlog.logerr('No account data found for referenced configuration ' + account.useconfig + ' (' + filename + ')')
				return None
	return account


def handleScheduledMails():
	""" This function is executed as a thread. It handles the sending of scheduled
		e-mails asynchronously.
	"""
	global	sleeptime, msgdir

	while True:
		ld = os.listdir(msgdir)

		for e in ld:
			ok = True
			try:
				fn = msgdir +  '/' + e
				try:
					mail = pickle.load(open(fn,'r'))
					if sendMail(mail, fn) == False:
						ok = False
						continue
				except:
					mlog.logerr('Reading mail caught exception: ' +  str(sys.exc_info()[0]) +": " + str(sys.exc_info()[1]))
					ok = False
					break
			finally:
				if ok:
					mlog.log("Removing scheduled file " + fn)
					os.remove(fn)
				else:
					if deleteonerror:
						mlog.log("Can't process mail. Removing " + fn)
						os.remove(fn)

		# finally, sleep till next time
		#mlog.log("------------------")
		time.sleep(sleeptime)

#############################################################################

def readConfig():
	""" Read the configuration from the configuration file in the current
		working directory.
	"""

	global smtpconfig, mailaccounts, port, msgdir,sleeptime, waitafterpop, debuglevel, deleteonerror

	if os.path.exists(configFile) == False:
		print('Configuration file "' + configFile +'" doesn''t exist. Exiting.')
		return False
	smtpconfig = config.Config()
	smtpconfig.read([configFile])

	# Read basic configuration
	port = smtpconfig.getint('config', 'port', default=port)							# port of the smtp proxy
	msgdir = smtpconfig.get('config', 'msgdir', default="./msgs")					# directory where to store temporary messages
	sleeptime = smtpconfig.getint('config', 'sleeptime', default=sleeptime)				# sleep time for sending thread
	waitafterpop = smtpconfig.getint('config', 'waitafterpop', default=waitafterpop)	# time to wait after pop authentication
	debuglevel = smtpconfig.getint('config', 'debuglevel', default=debuglevel)			# debuglevel for various functions
	deleteonerror = smtpconfig.getboolean('config', 'deleteonerror', default=deleteonerror)	# delete mail on error


	# Read accounts
	for s in smtpconfig.sections():
		if s not in [ 'logging', 'config' ]:
			account = MailAccount()

			account.useconfig = smtpconfig.get(s, 'use', default=account.useconfig)
			if account.useconfig != None:
				mailaccounts[s] = account
				continue

			account.rsmtphost = smtpconfig.get(s, 'smtphost', default=account.rsmtphost)
			account.rsmtpport = smtpconfig.getint(s, 'smtpport', default=account.rsmtpport)
			account.rsmtpsecurity = smtpconfig.get(s, 'smtpsecurity', default=account.rsmtpsecurity)
			account.rpophost = smtpconfig.get(s, 'pophost', default=account.rpophost)
			account.rpopport = smtpconfig.getint(s, 'popport', default=account.rpopport)
			account.rpopssl = smtpconfig.getboolean(s, 'popssl', default=account.rpopssl)
			account.rpopuser = smtpconfig.get(s, 'popusername', default=account.rpopuser)
			account.rpoppass = smtpconfig.get(s, 'poppassword', default=account.rpoppass)
			account.rPBS = smtpconfig.getboolean(s, 'popbeforesmtp', default=account.rPBS)
			account.rpopcheckdelay = smtpconfig.getint(s, 'popcheckdelay', default=account.rpopcheckdelay)
			account.rsmtpuser = smtpconfig.get(s, 'smtpusername', default=account.rsmtpuser)
			account.rsmtppass = smtpconfig.get(s, 'smtppassword', default=account.rsmtppass)
			account.localhostname = smtpconfig.get(s, 'localhostname', default=account.localhostname)
			account.returnpath = smtpconfig.get(s, 'returnpath', default=account.returnpath)
			account.replyto = smtpconfig.get(s, 'replyto', default=account.replyto)


			# check config
			if account.rsmtphost == None:
				mlog.logerr('Wrong configuration: smtphost is missing')
				return False
			if account.rPBS:
				if account.rpophost == None:
					mlog.logerr('Wrong configuration: pophost is missing')
					return False
				if account.rpopuser == None:
					mlog.logerr('Wrong configuration: popuser is missing')
					return False
				if account.rpoppass == None:
					mlog.logerr('Wrong configuration: poppass is missing')
					return False
			if account.rsmtpport == 0:	# Different default port depending on security type
				if account.rsmtpsecurity == 'none' or account.rsmtpsecurity == 'tls':
					account.rsmtpport = 25
				else:	# ssl
					account.rsmtpport = 465

			mailaccounts[s] = account

	# make temporary directory
	try:
		if os.path.exists(msgdir) == False:
			os.makedirs(msgdir)
	except:
		print('Can''t create message directory ' + msgdir)
		return False

	return True


def initLogging():
	"""Init the logging system.
	"""
	global smtpconfig, logFile, logSize, logCount, logLevel

	logFile = smtpconfig.get('logging', 'file', default=logFile)
	logSize = smtpconfig.getint('logging', 'size', default=logSize)
	logCount = smtpconfig.getint('logging', 'count', default=logCount)
	str = smtpconfig.get('logging', 'level', default='INFO')
	if str == 'NONE':
		logLevel = logging.CRITICAL
	if str == 'INFO':
		logLevel = logging.INFO
	if str == 'WARNING':
		logLevel = logging.WARNING
	if str == 'ERROR':
		logLevel = logging.ERROR
	if str == 'DEBUG':
		logLevel = logging.DEBUG
	return True


def loadMailHandlers():
	""" Import all mail handler from the specified directory, instanciate them, assign the logger,
		and put them into the list of mail handlers.
	"""
	sys.path.append(mailHandlerDir)
	for py in [f[:-3] for f in os.listdir(mailHandlerDir) if f.endswith('.py') and f != '__init__.py']:
		mod = __import__(py)
		classlist = [o for o in getmembers(mod, isclass)]
		for c in classlist:
			h = c[1]()
			if h.isEnabled():
				h.setLogger(mlog)
				mailHandlers[c[0]] = h
				mlog.log('Loaded mail handler "' + c[0] + '"')
	sys.path.remove(mailHandlerDir)


if __name__ == '__main__':

	if readConfig() == False:
		sys.exit(1)
	if initLogging() == False:
		sys.exit(1)
	mlog = mlogging.Logging(logFile, logSize, logCount, logLevel)
	if loadMailHandlers() == False:
		sys.exit(1)

	mlog.log('Starting SMTP Proxy on port ' + str(port))
	try:
		start_new_thread(handleScheduledMails, ())
		s = smtps.SMTPServer(port, mlog)
		s.serve(SMTPProxyService)
	except:
		mlog.logerr('Caught unknown exception: ' +  str(sys.exc_info()[0]) +": " + str(sys.exc_info()[1]))
		pass
