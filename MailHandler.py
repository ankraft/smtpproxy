#
# MailHander base class
#
# Author: Andreas Kraft (akr@mheg.org)
#
# DISCLAIMER
# You are free to use this code in any way you like, subject to the
# Python disclaimers & copyrights. I make no representations about the
# suitability of this software for any purpose. It is provided "AS-IS"
# without warranty of any kind, either express or implied. So there.
#
"""	Abstract Base class for MailHandler sub-classes. """
from abc import ABCMeta, abstractmethod

class MailHandler(object):
	__metaclass__ = ABCMeta

	@abstractmethod
	def isEnabled(self):
		"""Check whether the implementing handler should be executed.
		   This method must return True when the handler is enabled.
		"""
		pass

	@abstractmethod
	def setLogger(self, logger):
		"""This method is used to inject the logger instance into the handler.
		   The logger can be used to log results and debug messages from the handler.
		"""
		pass

	@abstractmethod
	def handleMessage(self, message):
		"""This message is called to handle a message. The message is an email 
		   object that conforms to the Python email library package. 
		   See [https://docs.python.org/2/library/email.html](https://docs.python.org/2/library/email.html) for details.
		"""
		pass
