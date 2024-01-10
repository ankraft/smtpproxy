#
# An extension of the ConfigParser class.
#
# Author: Andreas Kraft (akr@mheg.org)
#
# DISCLAIMER
# You are free to use this code in any way you like, subject to the
# Python disclaimers & copyrights. I make no representations about the
# suitability of this software for any purpose. It is provided "AS-IS"
# without warranty of any kind, either express or implied. So there.
#

import sys

"""An extended configuration file reader class.
"""
if sys.version_info[0] > 2:
    from configparser import *
else:
    from ConfigParser import *

class Config(ConfigParser):
	""" An extended configuration file reader class. This class extends
		some of the methods of the original ConfigParser class and
		provides them with the ability to return default values.
	 """

	if sys.version_info[0] > 2:
		def get(self, section, option, raw=False, vars=None, fallback=None, default=None):
			""" Get an option value for a given section. If the option or section
				is not found, return the value provided in default.

				The return value is a string.
			"""
			res = default
			if ConfigParser.has_option(self, section, option):
				res = ConfigParser.get(self, section, option, raw=raw, vars=vars, fallback=fallback)
			return res
	else:
		def get(self, section, option, default=None):
			""" Get an option value for a given section. If the option or section
				is not found, return the value provided in default.

				The return value is a string.
			"""
			res = default
			if ConfigParser.has_option(self, section, option):
				res = ConfigParser.get(self, section, option)
			return res

	def getboolean(self, section, option, default=None):
		""" Get an option value for a given section. If the option or section
			is not found, return the value provided in default.

			The return value is a boolean.
		"""
		res = default
		if ConfigParser.has_option(self, section, option):
			res = ConfigParser.getboolean(self, section, option)
		return res

	def getint(self, section, option, default=None):
		""" Get an option value for a given section. If the option or section
			is not found, return the value provided in default.

			The return value is an integer.
		"""
		res = default
		if ConfigParser.has_option(self, section, option):
			res = ConfigParser.getint(self, section, option)
		return res

	def getlist(self, section, option, default=None):
		""" Get an option value for a given section. If the option or section
			is not found, return the value provided in default. The value is
			treated as space separated list of keywords.

			The return value is a list of these values.
		"""
		res = default
		if ConfigParser.has_option(self, section, option):
			res = ConfigParser.get(self, section, option).strip()
			res = res.replace('\n', ' ')
			if ' ' in res:
				res = res.split(' ')
			else:
				res = [res]
			while '' in res:
				res.remove('')
		return res
