import os
import sublime
import functools
import threading
import subprocess
import time
import fcntl
# replace inprinter character in python
import string
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
    fd = self.proc.stdout.fileno()
    fl = fcntl.fcntl(fd, fcntl.F_GETFL)
    fcntl.fcntl(fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)
    lastline = ""
    while not self.proc.poll():
      try:
        # see http://stackoverflow.com/questions/92438/stripping-non-printable-characters-from-a-string-in-python
        for line in iter(self.proc.stdout.readline, ''):
          line = filter(lambda x: x in string.printable, line)
          if (lastline != line) :
            lastline = line
            main_thread(self.on_done, _make_text_safeish(line, self.fallback_encoding))
            LogEntry.getInstance().debug("in of reading new line - %s" % (line))
      except:
        time.sleep(1) 

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
      # LogEntry.getInstance().debug("runcommand for stdin - " + dcommand)
      self.proc.stdin.write(dcommand + "\n")
      self.proc.stdin.flush()
