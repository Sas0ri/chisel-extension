#!/usr/bin/python
# Example file with custom commands, located at /magical/commands/example.py

import lldb
import fblldbbase as fb
import fblldbobjcruntimehelpers as objc
import myhelper

def lldbcommands():
  return [ PrintSelector() ]
  
class PrintSelector(fb.FBCommand):
  def name(self):
    return 'psel'
    
  def description(self):
    return 'A command that prints selector of the address.'
    
  def run(self, arguments, options):
    # It's a good habit to explicitly cast the type of all return
    # values and arguments. LLDB can't always find them on its own.
    if len(arguments) > 0:
        lldb.debugger.HandleCommand('po SEL({})'.format(arguments[0]))
    else:        
        selector = myhelper.functionPreambleExpressionForSelector()
        lldb.debugger.HandleCommand('po SEL({})'.format(selector))

