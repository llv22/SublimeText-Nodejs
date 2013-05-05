import os
import subprocess
import sublime
import sublime_plugin
import re

import sys
if sys.modules.has_key('lib.command_thread'):
  del sys.modules['lib.command_thread']
if sys.modules.has_key('lib.command_logging'):
  del sys.modules['lib.command_logging']
if sys.modules.has_key('lib'):
  del sys.modules['lib']
import lib
from lib.command_thread import CommandThread
from lib.command_logging import LogEntry

# enable logging for sublime events
sublime.log_commands(True)

''' Nodejs of Sublime Text 2, run original commands
''' 
# when sublime loads a plugin it's cd'd into the plugin directory. Thus
# __file__ is useless for my purposes. What I want is "Packages/Git", but
# allowing for the possibility that someone has renamed the file.
# Fun discovery: Sublime on windows still requires posix path separators.
PLUGIN_DIRECTORY = os.getcwd().replace(os.path.normpath(os.path.join(os.getcwd(), '..', '..')) + os.path.sep, '').replace(os.path.sep, '/')
PLUGIN_PATH = os.getcwd().replace(os.path.join(os.getcwd(), '..', '..') + os.path.sep, '').replace(os.path.sep, '/')
# debugging command for reference
DEBUG_COMMANDS = ["run (r)", "cont (c)", "next (n)", "step (s)", "out (o)", "backtrace (bt)", "setBreakpoint (sb)", "clearBreakpoint (cb)", "watch", "unwatch", "watchers", "repl", "restart", "kill", "list", "scripts", "breakOnException", "breakpoints", "version"]

def open_url(url):
  sublime.active_window().run_command('open_url', {"url": url})

def view_contents(view):
  region = sublime.Region(0, view.size())
  return view.substr(region)

def plugin_file(name):
  return os.path.join(PLUGIN_DIRECTORY, name)

class NodeCommand(sublime_plugin.TextCommand):
  def run_command(self, command, callback=None, show_status=True, filter_empty_args=True, **kwargs):
    if filter_empty_args:
      command = [arg for arg in command if arg]
    if 'working_dir' not in kwargs:
      kwargs['working_dir'] = self.get_working_dir()
    s = sublime.load_settings("Nodejs.sublime-settings")
    if s.get('save_first') and self.active_view() and self.active_view().is_dirty():
      self.active_view().run_command('save')
    if command[0] == 'node' and s.get('node_command'):
      command[0] = s.get('node_command')
    if command[0] == 'npm' and s.get('npm_command'):
      command[0] = s.get('npm_command')
    if not callback:
      callback = self.generic_done

    # using thread for process interaction
    thread = CommandThread(command, callback, **kwargs)
    self.thread = thread
    thread.start()

    if show_status:
      message = kwargs.get('status_message', False) or ' '.join(command)
      sublime.status_message(message)

  def generic_done(self, result):
    if not result.strip():
      return
    self.panel(result)

  def _output_to_view(self, output_file, output, clear=False, syntax="Packages/JavaScript/JavaScript.tmLanguage"):
    output_file.set_syntax_file(syntax)
    edit = output_file.begin_edit()
    if clear:
      region = sublime.Region(0, self.output_view.size())
      output_file.erase(edit, region)
    output_file.insert(edit, 0, output)
    output_file.end_edit(edit)

  # in order to support appended into the end of text, orlando, 2013-04-30
  def _output_append_to_view_and_scrollend(self, output_file, output, clear=False, syntax="Packages/JavaScript/JavaScript.tmLanguage"):
    output_file.set_syntax_file(syntax)
    edit = output_file.begin_edit()
    if clear:
      region = sublime.Region(0, self.output_view.size())
      output_file.erase(edit, region)
    output_file.insert(edit, self.output_view.size(), output)
    output_file.end_edit(edit)
    self.output_view.show(self.output_view.size())

  # clean console
  def _clear_output_view(self):
    if not hasattr(self, 'output_view'):
      self.output_view = self.get_window().get_output_panel("git")
    edit = self.output_view.begin_edit()
    region = sublime.Region(0, self.output_view.size())
    self.output_view.erase(edit, region)

  def scratch(self, output, title=False, **kwargs):
    scratch_file = self.get_window().new_file()
    if title:
      scratch_file.set_name(title)
    scratch_file.set_scratch(True)
    self._output_to_view(scratch_file, output, **kwargs)
    scratch_file.set_read_only(True)
    return scratch_file

  # debugging for scratching
  def scratch_debug(self, output, title=False, **kwargs):
    scratch_file = self.get_window().new_file()
    if title:
      scratch_file.set_name(title)
    scratch_file.set_scratch(True)
    self._output_to_view(scratch_file, output, **kwargs)
    # scratch_file.set_read_only(True)
    return scratch_file

  def panel(self, output, **kwargs):
    if not hasattr(self, 'output_view'):
      self.output_view = self.get_window().get_output_panel("git")
    self.output_view.set_read_only(False)
    self._output_to_view(self.output_view, output, clear=True, **kwargs)
    self.output_view.set_read_only(True)
    self.output_view.set_name("debug_outputview")
    self.get_window().run_command("show_panel", {"panel": "output.git"})
    # move focus to show_panel - invalid
    self.get_window().focus_view(self.output_view)

  # python script for debugging case - http://www.sublimetext.com/docs/2/api_reference.html
  def panel_debug(self, output, **kwargs):
    if not hasattr(self, 'output_view'):
      self.output_view = self.get_window().get_output_panel("git")
    self.output_view.set_name("debug_outputview")
    self.output_view.set_read_only(False)
    self._output_append_to_view_and_scrollend(self.output_view, output, clear=False, **kwargs)
    # can we capature events here?
    # self.output_view.set_read_only(True)
    self.get_window().run_command("show_panel", {"panel": "output.git"})
    # move focus to show_panel - invalid
    self.get_window().focus_view(self.output_view)

  def quick_panel(self, *args, **kwargs):
    self.get_window().show_quick_panel(*args, **kwargs)

# A base for all git commands that work with the entire repository
class NodeWindowCommand(NodeCommand, sublime_plugin.WindowCommand):
  def active_view(self):
    return self.window.active_view()

  def _active_file_name(self):
    view = self.active_view()
    if view and view.file_name() and len(view.file_name()) > 0:
      return view.file_name()

  # If there's no active view or the active view is not a file on the
  # filesystem (e.g. a search results view), we can infer the folder
  # that the user intends Git commands to run against when there's only
  # only one.
  def is_enabled(self):
    if self._active_file_name() or len(self.window.folders()) == 1:
      return os.path.realpath(self.get_working_dir())

  def get_file_name(self):
    return ''

  # If there is a file in the active view use that file's directory to
  # search for the Git root.  Otherwise, use the only folder that is
  # open.
  def get_working_dir(self):
    file_name = self._active_file_name()
    if file_name:
      return os.path.dirname(file_name)
    else:
      return self.window.folders()[0]

  def get_window(self):
    return self.window

# A base for all git commands that work with the file in the active view
class NodeTextCommand(NodeCommand, sublime_plugin.TextCommand):
  def active_view(self):
    return self.view

  def is_enabled(self):
    # First, is this actually a file on the file system?
    if self.view.file_name() and len(self.view.file_name()) > 0:
      return os.path.realpath(self.get_working_dir())

  def get_file_name(self):
    return os.path.basename(self.view.file_name())

  def get_working_dir(self):
    return os.path.dirname(self.view.file_name())

  def get_window(self):
    # Fun discovery: if you switch tabs while a command is working,
    # self.view.window() is None. (Admittedly this is a consequence
    # of my deciding to do async command processing... but, hey,
    # got to live with that now.)
    # I did try tracking the window used at the start of the command
    # and using it instead of view.window() later, but that results
    # panels on a non-visible window, which is especially useless in
    # the case of the quick panel.
    # So, this is not necessarily ideal, but it does work.
    return self.view.window() or sublime.active_window()

# Commands to run


# Command to build docs
class NodeBuilddocsCommand(NodeTextCommand):
  def run(self, edit):
    doc_builder = os.path.join(PLUGIN_PATH, 'tools/default_build.js')
    command = ['node', doc_builder]
    self.run_command(command, self.command_done)

  def command_done(self, result):
    s = sublime.load_settings("Nodejs.sublime-settings")
    if s.get('output_to_new_tab'):
      self.scratch(result, title="Node Output", syntax="Packages/JavaScript/JavaScript.tmLanguage")
    else:
      self.panel(result)

# Command to Run node
class NodeRunCommand(NodeTextCommand):
  def run(self, edit):
    command = """kill -9 `ps -ef | grep node | grep -v grep | awk '{print $2}'`"""
    os.system(command)
    command = ['node', self.view.file_name()]
    self.run_command(command, self.command_done)

  def command_done(self, result):
    s = sublime.load_settings("Nodejs.sublime-settings")
    if s.get('output_to_new_tab'):
      self.scratch(result, title="Node Output", syntax="Packages/JavaScript/JavaScript.tmLanguage")
    else:
      self.panel(result)

# Command to run node with debug
class NodeDrunCommand(NodeTextCommand):
  def run(self, edit):
    # clear-up debug console
    # LogEntry.getInstance().debug("clean output UI")
    self._clear_output_view()
    command = """kill -9 `ps -ef | grep node | grep -v grep | awk '{print $2}'`"""
    os.system(command)
    command = ['node', 'debug', self.view.file_name()]
    self.run_command(command, self.command_done)

  def command_done(self, result):
    s = sublime.load_settings("Nodejs.sublime-settings")
    if s.get('output_to_new_tab'):
      self.scratch_debug(result, title="Node Output", syntax="Packages/JavaScript/JavaScript.tmLanguage")
    else:
      self.panel_debug(result)
    self.quick_panel(DEBUG_COMMANDS, self.on_input_debug, sublime.MONOSPACE_FONT)

  def on_input_debug(self, command):
    if command == -1:
      return
    if not hasattr(self, 'output_view'):
      self.output_view = self.get_window().get_output_panel("git")
    self.output_view.set_read_only(False)
    debug_inui = "debug> %s\n" % (DEBUG_COMMANDS[command])
    self._output_append_to_view_and_scrollend(self.output_view, debug_inui, clear=False)
    self.output_view.set_read_only(True)
    # interaction with process
    if not (self.thread is None):
      c = re.sub(r'\([^)]*\)', '', DEBUG_COMMANDS[command]).strip()
      self.thread.rundcommand(c)

""" Command to run node with arguments
"""
class NodeRunArgumentsCommand(NodeTextCommand):
  def run(self, edit):
    self.get_window().show_input_panel("Arguments", "", self.on_input, None, None)

  def on_input(self, message):
    command = message.split()
    command.insert(0, self.view.file_name());
    command.insert(0, 'node');
    self.run_command(command, self.command_done)

  def command_done(self, result):
    self.scratch(result, title="Node Output", syntax="Packages/JavaScript/JavaScript.tmLanguage")

# Command to run node with debug and arguments
class NodeDrunArgumentsCommand(NodeTextCommand):
  def run(self, edit):
    self.get_window().show_input_panel("Arguments", "", self.on_input, None, None)

  def on_input(self, message):
    command = message.split()
    command.insert(0, self.view.file_name());
    command.insert(0, 'debug');
    command.insert(0, 'node');
    self.run_command(command, self.command_done)

  def command_done(self, result):
    s = sublime.load_settings("Nodejs.sublime-settings")
    if s.get('output_to_new_tab'):
      self.scratch(result, title="Node Output", syntax="Packages/JavaScript/JavaScript.tmLanguage")
    else:
      self.panel(result)

class NodeNpmCommand(NodeTextCommand):
  def run(self, edit):
    self.get_window().show_input_panel("Arguments", "", self.on_input, None, None)

  def on_input(self, message):
    command = message.split()
    command.insert(0, "npm");
    self.run_command(command, self.command_done)

  def command_done(self, result):
    s = sublime.load_settings("Nodejs.sublime-settings")
    if s.get('output_to_new_tab'):
      self.scratch(result, title="Node Output", syntax="Packages/Text/Plain text.tmLanguage")
    else:
      self.panel(result)

class NodeNpmInstallCommand(NodeTextCommand):
  def run(self, edit):
    self.run_command(['npm', 'install'], self.command_done)

  def command_done(self, result):
    s = sublime.load_settings("Nodejs.sublime-settings")
    if s.get('output_to_new_tab'):
      self.scratch(result, title="Node Output", syntax="Packages/Text/Plain text.tmLanguage")
    else:
      self.panel(result)

class NodeNpmUninstallCommand(NodeTextCommand):
  def run(self, edit):
    self.get_window().show_input_panel("Package", "", self.on_input, None, None)

  def on_input(self, message):
    command = message.split()
    command.insert(0, "npm");
    command.insert(1, "uninstall")
    self.run_command(command, self.command_done)

  def command_done(self, result):
    s = sublime.load_settings("Nodejs.sublime-settings")
    if s.get('output_to_new_tab'):
      self.scratch(result, title="Node Output", syntax="Packages/Text/Plain text.tmLanguage")
    else:
      self.panel(result)

class NodeNpmSearchCommand(NodeTextCommand):
  def run(self, edit):
    self.get_window().show_input_panel("Term", "", self.on_input, None, None)

  def on_input(self, message):
    command = message.split()
    command.insert(0, "npm");
    command.insert(1, "search")
    self.run_command(command, self.command_done)

  def command_done(self, result):
    s = sublime.load_settings("Nodejs.sublime-settings")
    if s.get('output_to_new_tab'):
      self.scratch(result, title="Node Output", syntax="Packages/Text/Plain text.tmLanguage")
    else:
      self.panel(result)

class NodeNpmPublishCommand(NodeTextCommand):
  def run(self, edit):
    self.run_command(['npm', 'publish'], self.command_done)

  def command_done(self, result):
    s = sublime.load_settings("Nodejs.sublime-settings")
    if s.get('output_to_new_tab'):
      self.scratch(result, title="Node Output", syntax="Packages/Text/Plain text.tmLanguage")
    else:
      self.panel(result)

class NodeNpmUpdateCommand(NodeTextCommand):
  def run(self, edit):
    self.run_command(['npm', 'update'], self.command_done)

  def command_done(self, result):
    s = sublime.load_settings("Nodejs.sublime-settings")
    if s.get('output_to_new_tab'):
      self.scratch(result, title="Node Output", syntax="Packages/Text/Plain text.tmLanguage")
    else:
      self.panel(result)

class NodeNpmListCommand(NodeTextCommand):
  def run(self, edit):
    self.run_command(['npm', 'ls'], self.command_done)

  def command_done(self, result):
    s = sublime.load_settings("Nodejs.sublime-settings")
    if s.get('output_to_new_tab'):
      self.scratch(result, title="Node Output", syntax="Packages/Text/Plain text.tmLanguage")
    else:
      self.panel(result)

class NodeUglifyCommand(NodeTextCommand):
  def run(self, edit):
    uglify = os.path.join(PLUGIN_PATH, 'tools/uglify_js.js')
    command = ['node', uglify, '-i', self.view.file_name()]
    self.run_command(command, self.command_done)

  def command_done(self, result):
    s = sublime.load_settings("Nodejs.sublime-settings")
    if s.get('output_to_new_tab'):
      self.scratch(result, title="Node Output", syntax="Packages/JavaScript/JavaScript.tmLanguage")
    else:
      self.panel(result)

''' Debugging console for Nodejs of Sublime Text 2, Orlando, 2013-05
''' 

# core implemention for CaptureEditing
# see discussion - http://www.sublimetext.com/forum/viewtopic.php?f=6&t=10457
# see mouse event - https://github.com/SublimeText/MouseEventListener/blob/master/mouse_event_listener.py
class CaptureEditing(sublime_plugin.EventListener):
  edit_info = {}

  # check-up if current view is output panel for our debugging
  def __isNodeJsDebugOutputView(self, view):
    if not view: 
      return False
    return (view is not None and view.name() == "debug_outputview")

  def on_modified(self, view):
    if not self.__isNodeJsDebugOutputView(view):
      # I only want to use views, not the input-panel, etc..
      print "hint here for return"
      return False
    print "hint here for submiting changes"
    vid = view.id()
    if not CaptureEditing.edit_info.has_key(vid):
      # create a dictionary entry based on the current views' id
      CaptureEditing.edit_info[vid] = {}
    cview = CaptureEditing.edit_info[vid]
    # I can now store details of the current edit in the edit_info dictionary, via cview.

  def on_query_context(self, view, key, operator, operand, match_all):
    # query nodejs_drun and panel, then give for on_modified
    print "on_query_context - view : %s, key : %s, operator : %s, operand : %s" % (view.name(), key, operator, operand)
    return None

# # click for only for this js project
# class NodejsDebugClick(sublime_plugin.TextCommand):
#   def run(self, args):
#     print "NodejsDebugClick"

# # double-click for only for this js project
# class NodejsDebugDoubleClick(sublime_plugin.TextCommand):
#   def run(self, args):
#     print "NodejsDebugDoubleClick"