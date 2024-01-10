#
#	FixAddress.py
#	Mail handler for replacing the to: field
#

import mlogging, sys
from email.header import decode_header
import MailHandler


class FixAddress(MailHandler.MailHandler):

	logger	= None
	toToFix = '<name@some.address.com>'
	newTo 	= '<other.name@new.address.com>'

	def isEnabled(self):
		return False;

	def setLogger(self, logger):
		self.logger = logger

	def handleMessage(self, message, mail, callback):
		if mail.to[0] == self.toToFix:
			self.logger.log('FixAddress: Changing to: field for ' + mail.to[0] + ' -> ' + self.newTo)
			callback.setTo(self.newTo)
		return True

