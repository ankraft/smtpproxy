#
#	SaveNewPhoneMessage.py
#	Mail handler for saving a new message from the FritzBox
#

import mlogging, sys
from email.header import decode_header
import MailHandler


class SaveNewPhoneMessage(MailHandler.MailHandler):

	directory = '/media/sf_DebianExchange/Anrufe'
	defaultFilename = "message.wav"
	logger = None

	def isEnabled(self):
		return False

	def setLogger(self, logger):
		self.logger = logger

	def handleMessage(self, message, mail, callback):
		subject, _ = decode_header(message['subject'])[0]	# decode utf-8 if necessary
		self.logger.log('SaveNewPhoneMessage: handling message with subject ' + subject)
		try:
			if subject.startswith('Nachricht von'):
				part = message.get_payload(1)	# magic
				filename = self.directory + '/' + part.get_filename(self.defaultFilename)
				self.logger.log('Saving message to ' + filename)
				fp = open(filename, 'wb')
				fp.write(part.get_payload(None, True))
				fp.close()
		except:
			self.logger.logerr('Saving file caught exception: ' +  str(sys.exc_info()[0]) +": " + str(sys.exc_info()[1]))
		return True

