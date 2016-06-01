#!/usr/bin/env python

import sys, os
import tempfile, shutil, glob
from common import runLocalCommand as run


def parse_args(args):
  from optparse import OptionParser
  parser = OptionParser('''update_distribution_package.py <current_package>

  A current distribution package must be available for update. If a path
  is not provided, the script will attempt the following paths in order:

    $NAO_HOME/install/caffe-32.tar.gz
    /mnt/share/caffe-32.tar.gz
    ./caffe-32.tar.gz

  If no distribution package is found the script will exit.
  ''')

  options,args = parser.parse_args(args)
  return options, args

def find_current(args):
  if len(args) > 0:
    p = args[0]
    if os.path.isfile(p):
      print 'Using supplied package at %s' % p
      return p

    raise Exception("Invalid package: %s" % p)
  searches = map(os.path.expandvars, [
    '$NAO_HOME/install/caffe-32.tar.gz',
    '/mnt/share/caffe-32.tar.gz',
    './caffe-32.tar.gz',
  ])
  for p in searches:
    if os.path.isfile(p):
      print 'Found package at %s' % p
      return p
  raise Exception("No valid package found.")

def update_package(package):
  # Create a temp directory for modifying the package
  tempdir = tempfile.mkdtemp()
  print "Current directory: %s" % os.getcwd()
  # General script layout prior to editing
  script = '''
    git pull
    cp Makefile.config.example Makefile.config
    make -j6
    make -j6 pycaffe
    make -j6 distribute
    tar zxvf {pkg} -C {tmp}
    cp -ar {{dist_file}} {tmp}/caffe-32/caffe
    tar zcvf {pkg} -C {tmp} caffe-32
  '''.format(pkg=package, tmp=tempdir).strip()
  # Trim whitespace and expand special characters
  maps = [str.strip, os.path.expanduser, os.path.expandvars]
  commands = script.split('\n')
  for m in maps:
    commands = map(m, commands)
  # Wildcards can't be expanded like above so 
  # instead we iterate over them and re-insert
  # the commands with glob
  copy_cmd = commands.pop(-2)
  for g in glob.iglob('distribute/*'):
    commands.insert(-1, copy_cmd.format(dist_file=g))
  # Run all the commands and exit immediately on error
  for cmd in commands:
    print "Running command: ",cmd
    run(cmd,output=True,exit_on_error=True)
  shutil.rmtree(tempdir)

def goto_repo_root():
  script_dir = os.path.dirname(os.path.realpath(__file__))
  os.chdir(script_dir)
  root_dir = run("git rev-parse --show-toplevel",output=False)
  os.chdir(root_dir)
  print "goto %s" % root_dir

if __name__ == '__main__':
  options, args = parse_args(sys.argv[1:])
  current = find_current(args)
  goto_repo_root()
  update_package(current)
