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

Bug lists
---------------
* #1. Python singleton logging utilise with multi-time output for one single logging event (debug()..)


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


