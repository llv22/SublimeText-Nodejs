import os
import sublime
import functools
import threading
import subprocess
import time
import fcntl
import inspect
# replace inprinter character in python
import string
import sys
if sys.modules.has_key('command_logging'):
  del sys.modules['command_logging']
from command_logging import LogEntry

def main_thread(callback, *args, **kwargs):
  # sublime.set_timeout gets used to send things onto the main thread
  # most sublime.[something] calls need to be on the main thread
  sublime.set_timeout(functools.partial(callback, *args, **kwargs), 0)

def _make_text_safeish(text, fallback_encoding):
  # The unicode decode here is because sublime converts to unicode inside
  # insert in such a way that unknown characters will cause errors, which is
  # distinctly non-ideal... and there's no way to tell what's coming out of
  # git in output. So...
  try:
    unitext = text.decode('utf-8')
  except UnicodeDecodeError:
    unitext = text.decode(fallback_encoding)
  return unitext

class CommandThread(threading.Thread):
  def __init__(self, command, on_done, working_dir="", fallback_encoding=""):
    threading.Thread.__init__(self)
    self.command = command
    self.on_done = on_done
    self.working_dir = working_dir
    self.fallback_encoding = fallback_encoding

  def worker(self):
    # see non-block io programming for subprocess - http://stackoverflow.com/questions/375427/non-blocking-read-on-a-subprocess-pipe-in-python
    flags = self.proc.stdout.fileno()
    fl = fcntl.fcntl(flags, fcntl.F_GETFL)
    fcntl.fcntl(flags, fcntl.F_SETFL, fl | os.O_NONBLOCK)
    ex = True
    while not self.proc.poll():
      try:
        ex = False
        # see http://stackoverflow.com/questions/92438/stripping-non-printable-characters-from-a-string-in-python
        for line in iter(self.proc.stdout.readline, ''):
          line = filter(lambda x: x in string.printable, line)
          LogEntry.getInstance().debug("(%s) %s" % (self.stacktrace(), line))
          main_thread(self.on_done, _make_text_safeish(line, self.fallback_encoding))
      except:
        ex = True
      finally:
        if ex:
          # bug - AttributeError: 'NoneType' object has no attribute 'sleep'
          # https://github.com/chartbeat/mongo-python-driver/commit/a3ee17cadc6811538fdda5c3b8c9942a1a25d2bd
          # change 1 to 0.6 for better reaction in UI
          time.sleep(0.6)

  def run(self):
    try:
      # Per http://bugs.python.org/issue8557 shell=True is required to
      # get $PATH on Windows. Yay portable code.
      shell = os.name == 'nt'
      if self.working_dir != "":
        os.chdir(self.working_dir)
      proc = subprocess.Popen(self.command,
         stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.STDOUT,
         shell=shell, universal_newlines=True)
      # save reference for debugging interaction
      self.proc = proc
      t = threading.Thread(target=self.worker)
      t.daemon = True
      t.start()
      self.proc.wait()
      ''' preivous standard implementation - orlando, 2013-04-30
      output = proc.communicate()[0]
      # if sublime's python gets bumped to 2.7 we can just do:
      # output = subprocess.check_output(self.command)
      main_thread(self.on_done, _make_text_safeish(output, self.fallback_encoding))
      '''
    except subprocess.CalledProcessError, e:
      main_thread(self.on_done, e.returncode)
    except OSError, e:
      if e.errno == 2:
        main_thread(sublime.error_message, "Node binary could not be found in PATH\n\nConsider using the node_command setting for the Node plugin\n\nPATH is: %s" % os.environ['PATH'])
      else:
        raise e

  """ runcommand with debugging interaction via process.stdin for write  
  """ 
  def rundcommand(self, dcommand):
    if (self.proc is None):
      return
    else:
      self.proc.stdin.write(dcommand + "\n")
      self.proc.stdin.flush()

  def killself(self):
    if self.proc:
      self.proc.terminate()

  """ __line__, __function__ in python  
  see http://stackoverflow.com/questions/6810999/how-to-determine-file-function-and-line-number
  """ 
  def stacktrace(self):
    # 0 represents this line, 1 represents line at caller
    callerframerecord = inspect.stack()[1]                    
    frame = callerframerecord[0]
    info = inspect.getframeinfo(frame)
    cstack = ("%s %s:%s") % (info.filename, info.function, info.lineno)
    return cstack
