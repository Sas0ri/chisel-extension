import lldb
import fblldbbase as fb
import fblldbobjcruntimehelpers as objc

import sys
import os
import re

def lldbcommands():
  return [ MyMethodBreakpointCommand() ]

class MyMethodBreakpointCommand(fb.FBCommand):
  def name(self):
    return 'bmsg'

  def description(self):
    return "Set a breakpoint for a selector on a class, even if the class itself doesn't override that selector. It walks the hierarchy until it finds a class that does implement the selector and sets a conditional breakpoint there."

  def args(self):
    return [
      fb.FBCommandArgument(arg='expression', type='string', help='Expression to set a breakpoint on, e.g. "-[MyView setFrame:]", "+[MyView awesomeClassMethod]" or "-[0xabcd1234 setFrame:]"'),
    ]

  def run(self, arguments, options):
    expression = arguments[0]

    methodPattern = re.compile(r"""
      (?P<scope>[-+])?
      \[
        (?P<target>.*?)
        (?P<category>\(.+\))?
        \s+
        (?P<selector>.*)
      \]
        """, re.VERBOSE)

    match = methodPattern.match(expression)

    if not match:
      print ('Failed to parse expression. Do you even Objective-C?!')
      return
    
    methodTypeCharacter = match.group('scope')
    classNameOrExpression = match.group('target')
    category = match.group('category')
    selector = match.group('selector')

    methodIsClassMethod = (methodTypeCharacter == '+')

    if not methodIsClassMethod:
      # The default is instance method, and methodTypeCharacter may not actually be '-'.
      methodTypeCharacter = '-'

    targetIsClass = False
    targetObject = fb.evaluateObjectExpression('({})'.format(classNameOrExpression), False)

    if not targetObject:
      # If the expression didn't yield anything then it's likely a class. Assume it is.
      # We will check again that the class does actually exist anyway.
      targetIsClass = True
      targetObject = fb.evaluateObjectExpression('[{} class]'.format(classNameOrExpression), False)

    targetClass = fb.evaluateObjectExpression('[{} class]'.format(targetObject), False)

    if not targetClass or int(targetClass, 0) == 0:
      print ('Couldn\'t find a class from the expression "{}". Did you typo?'.format(classNameOrExpression))
      return

    if methodIsClassMethod:
      targetClass = objc.object_getClass(targetClass)

    found = False
    nextClass = targetClass

    while not found and int(nextClass, 0) > 0:
      if classItselfImplementsSelector(nextClass, selector):
        found = True
      else:
        nextClass = objc.class_getSuperclass(nextClass)

    if not found:
      print ('There doesn\'t seem to be an implementation of {} in the class hierarchy. Made a boo boo with the selector name?'.format(selector))
      return

    address = 0x00
    if methodIsClassMethod:
        address = class_getClassMethodImplementation(targetClass, selector)
    else:
        address = class_getInstanceMethodImplementation(targetClass,selector)

    lldb.debugger.HandleCommand('breakpoint set -a{}'.format(address))
    

def class_getClassMethodImplementation(klass,selector):
  command = '(void*)class_getClassMethod({},@selector({}))'.format(klass,selector)
  method = fb.evaluateExpression(command)
  command = '(void*)method_getImplementation({})'.format(method)
  imp = fb.evaluateExpression(command)
  return imp

def class_getInstanceMethodImplementation(klass,selector):
  command = '(void*)class_getInstanceMethod({},@selector({}))'.format(klass,selector)
  method = fb.evaluateExpression(command)
  command = '(void*)method_getImplementation({})'.format(method)
  imp = fb.evaluateExpression(command)
  return imp

def classItselfImplementsSelector(klass, selector):
  thisMethod = objc.class_getInstanceMethod(klass, selector)
  if thisMethod == 0:
    return False

  superklass = objc.class_getSuperclass(klass)
  superMethod = objc.class_getInstanceMethod(superklass, selector)
  if thisMethod == superMethod:
    return False
  else:
    return True