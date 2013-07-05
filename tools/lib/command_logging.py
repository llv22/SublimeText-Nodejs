import logging
from logging.handlers import TimedRotatingFileHandler
import string
import os

class LogEntry(object):
	_singletons = {}
	_logfilename = "/Users/llv22/Documents/00_python/SublimeText-test/sub2nodejs.log"
	record = 0
	def __new__(cls, *args, **kwds):
		if cls not in cls._singletons:
			proxy = super(LogEntry, cls).__new__(cls)
			logger = logging.getLogger('sublimeplugin')
			logger.setLevel(logging.DEBUG)
			# bug 0 - add repeated item into context, perhaps for ctrl+D, new plugin object will load LogEntry() item
			if not len(logger.handlers):
				hdlr = TimedRotatingFileHandler(LogEntry._logfilename, when="midnight", interval=1, backupCount=3)
				hdlr.suffix = "%Y-%m-%d"
				formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
				hdlr.setFormatter(formatter)
				logger.addHandler(hdlr) 
			cls._singletons[cls] = proxy
			# must give value for singleton of python, here - have to refine for thread-safety
			proxy._singletonlogger = logger
		return cls._singletons[cls]

	# empty ctor, see also private method - http://stackoverflow.com/questions/70528/why-are-pythons-private-methods-not-actually-private
	def __init__(self):
		pass

	@staticmethod
	def getInstance():
		return LogEntry.__new__(LogEntry)

	""" instance method, not for class
	"""
	def debug(self, info):
		logstr = "[%s] %s " % (LogEntry.record, info.rstrip(string.whitespace))
		LogEntry.getInstance()._singletonlogger.debug(logstr)
		LogEntry.record = LogEntry.record + 1