Nodejs Sublime Text 2 Package
=============================

# Debugging utilities for fun

This project is on top of tanepiper's SublimeText-Nodejs. I'd like to add javascript debugging into sublime text 2. No plan for Sublime Text 3 now.

Overview
--------
The Nodejs Sublime Text 2 Package provides a set of code completion, scripts and tools to work with
[nodejs](http://nodejs.org).

Screen shot
--------------
when you invoke ctrl+D for javascript debugging, after debugging start, you will see quick-screen in your javascript view. just select item then output will be displayed in output view.

![debugging screen](https://raw.github.com/llv22/SublimeText-Nodejs/master/screenshots/Screenshot.jpg)

Debugging
---------------
* Python non-block IO for interaction of friendly-debugging
  
  1, basic debugging with subprocess interaction - [almost done]
  
  2, invoke debugging quick-show via short-cut - [?]
  
  3, allow to enter debug commands in output view - [?]

	*technically core of this is to avoid erase the previous text content, is it possible to ? [have to check-up]*
  
  4, allow to enter debug commands in output view - [?]
  
  5, code refactoring and short-cut command to invoke menu - [?]

Utilities for development
---------------
* Logging for python framework debugging
  
  status - done

Bug lists
---------------
* BUG-0, Python singleton logging utilise with multi-time output for one single logging event (debug()..)

  status - find root reason

  reason - when using ctrl+D repeatedly in console, LogEntry.getInstance() will be create again, however, the existing instance still be invoked. multi-handler will be instantiated repeatedly, so add handlers check-up

  solution - check handlers length and force to skip

  workaround - quit sublime framework, and reload to guarantee the existing instance of logger has been fanlized

* BUG-1, AttributeError: 'NoneType' object has no attribute 'sleep' in command_thread.py line 60

  status - fixed

  solution - see reference in https://github.com/chartbeat/mongo-python-driver/commit/a3ee17cadc6811538fdda5c3b8c9942a1a25d2bd. control exception via boolean, and sleep not in handling exception loop [? why, to check python source code of exception handling]

Status
--------------
In development of v0, not ready for release

Install
-------
You may install `Nodejs` via the [Sublime Text 2 package manager](http://wbond.net/sublime_packages/package_control),
or using git with the below commands:

*MacOSX*

    `git clone git://github.com/tanepiper/SublimeText-Nodejs.git ~/Library/Application\ Support/Sublime\ Text\ 2/Packages/Nodejs`

*Windows*

    `git clone https://github.com/tanepiper/SublimeText-Nodejs "%APPDATA%\Sublime Text 2\Packages\Nodejs"`

Author & Contributors
----------------------
[Tane Piper](http://twitter.com/tanepiper) - Sponsor, donate to my Sublime Text 2 licence fund

[Orlando Ding](http://weibo.com/orlando22) - All outputs in private time for fun, thanks for Tane's great basis framework

