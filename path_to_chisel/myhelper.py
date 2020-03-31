import fblldbobjcruntimehelpers as objc

def functionPreambleExpressionForSelector():
  import re

  arch = objc.currentArch()
  expressionForSelector = None
  if arch == 'i386':
    expressionForSelector = '*(id*)($esp+8)'
  elif arch == 'x86_64':
    expressionForSelector = '(id)$rsi'
  elif arch == 'arm64':
    expressionForSelector = '(id)$x1'
  elif re.match(r'^armv.*$', arch):
    expressionForSelector = '(id)$r1'
  return expressionForSelector