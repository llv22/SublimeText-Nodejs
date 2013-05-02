import logging

class LogEntry(object):
	_singletons = {}
	_singleton = None
	record = 0
	def __new__(cls, *args, **kwds):
		if cls not in cls._singletons:
			proxy = super(LogEntry, cls).__new__(cls)
			# setter for internal field
			logger = logging.getLogger('sublimeplugin')
			hdlr = logging.FileHandler("/Users/llv22/Documents/03_java_javascript/04_javascript/00_releasegithub/sublimeplugin_runtime.log")
			formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
			hdlr.setFormatter(formatter)
			logger.addHandler(hdlr) 
			logger.setLevel(logging.DEBUG)
			proxy.logger = logger
			cls._singletons[cls] = proxy
			_singleton = proxy
		return cls._singletons[cls]

	@staticmethod
	def getInstance():
		if (LogEntry._singleton is None):
			LogEntry._singleton = LogEntry()
		return LogEntry._singleton

	""" instance method, not for class
	"""
	def debug(self, info):
		proxy = LogEntry.getInstance()
		logstr = "[t-%s] %s " % (LogEntry.record, info)
		proxy.logger.debug(logstr)
		LogEntry.record = LogEntry.record + 1