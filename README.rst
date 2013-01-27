*kajak* is a tiny command-line calendar tool.

.. warning::
   This software is in early stage of development. Use at your own risk!

Data model
----------
Each task is assigned a *date* and a descriptive *text*. Every (*date*,
*text*) tuple is required to be unique; that is, if two tasks have share the
*date*, their *text*\s must be different.

Bugs
----
The behavior is undefined if this program is running while the current date
changes.
