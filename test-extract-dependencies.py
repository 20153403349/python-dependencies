from dependencies import extract_package
import xmlrpc.client as xmlrpclib
import itertools as it
import random

client = xmlrpclib.ServerProxy('http://pypi.python.org/pypi')
to='test-pypi-deps.txt'
packages = ['gala', 'scikit-learn', 'scipy', 'scikit-image', 'Flask']
random.shuffle(packages)

# Check if package is already in the output file (useful for restarting after a failure)
try:
    with open(to, 'r') as fin:
        done_packages = set([line.split()[0] for line in fin])
except FileNotFoundError:
    done_packages = set()

# initalising variables for progress bar
i = 0
n = len(packages)
prev_percent_done = 0

for package in packages:
    if package not in done_packages:
        extract_package(package, to=to, client=client)

    # progress bar
    i += 1
    percent_done = round(i/n*100)
    if percent_done > prev_percent_done:
        print('{0}% done ({1} of {2})'.format(percent_done,i,n))
        prev_percent_done = percent_done
