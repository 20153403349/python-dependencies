"""Get dependencies from packages on the Python Package Index (PyPI)

Adapted from Olivier Girardot's notebook:

https://github.com/ogirardot/meta-deps/blob/master/PyPi%20Metadata.ipynb

licensed under the Creative Commons Attribution 3.0 Unported License.

To view a copy of that license, visit
http://creativecommons.org/licenses/by/3.0/

Changes:
- Read import statements in all .py files, instead of install_requires list in
  setup.py
- Read zip files instead of tar files
- Don't produce graph
- Remove json
"""

import xmlrpc.client as xmlrpclib
import re, requests, csv, zipfile

def compression_type(filename):
    """ Test which type of compressed file it is
    adapted from http://stackoverflow.com/a/13044946 """

    compression_dict = {
        "\x1f\x8b\x08": "gz",
        "\x42\x5a\x68": "bz2",
        "\x50\x4b\x03\x04": "zip",
        "\x1f\x9d": "tar"
        }

    max_len = max(len(x) for x in compression_dict)

    try:
        with open(filename) as f:
            file_start = f.read(max_len)
    except UnicodeDecodeError:
        with open(filename, encoding="latin-1") as f:
            file_start = f.read(max_len)

    for sig, filetype in compression_dict.items():
        if file_start.startswith(sig):
            return filetype
    return None

def extract_dependencies(content):
    """Extract dependencies by parsing import statements"""
    deps = set()
    for line in content.split('\n'):
        line = line.strip()  # we don't care about indentation
        if not (line.startswith("from") or
                line.startswith("import")):
            continue
        if (line.startswith('#') or line.startswith('"""') or
                line.startswith("'''")):
            continue
        if '#' in line:
            line = line.split("#", 1)[0].strip()
        if line.startswith('from'):  # from foo import bar
            matches = re.findall("from (.*?)(?: import)", line)
        else:  # import foo
            matches = re.findall("import (.*?)(?:$| as)", line)
        for match in matches:
            for x in match.split(','):
                if not x.startswith('.'):
                    deps.add(x)
    return deps

def _extract_content(package_file):
    """Extract content from compressed package - .py files only"""
    try:
        zip_file = zipfile.ZipFile(package_file)
    except:
        return None
    py_files = [elem for elem in zip_file.namelist() if '.py' in elem]
    for py_file in py_files:
        try:
            content = zip_file.read(py_file).decode()
            yield content
        except:
            #print('trouble decoding')
            yield None


DEFAULT_CLIENT = xmlrpclib.ServerProxy('http://pypi.python.org/pypi')


def extract_package(name, client=DEFAULT_CLIENT, n=0):
    tmpfilename = '/tmp/temp_py_package_{0}.zip'.format(n)
    with open('pypi-deps.txt', 'a') as file:
        spamwriter = csv.writer(file, delimiter='\t',
                            quotechar='|', quoting=csv.QUOTE_MINIMAL)
        releases = client.package_releases(name)
        if len(releases) == 0:
            return
        release = client.package_releases(name)[0]  # use only latest release
        doc = client.release_urls(name, release)
        if doc:
            url = doc[0].get('url')
            req = requests.get(url)
            if req.status_code != 200:
                print("Could not download file %s" % req.status_code)
            else:
                with open(tmpfilename, 'wb') as zip_file:
                    zip_file.write(req.content)
                with open(tmpfilename, 'rb') as zip_file:
                    dependencies = set()
                    for content in _extract_content(zip_file):
                        dependencies.update(extract_dependencies(content))
                    for dep in dependencies:
                        spamwriter.writerow([name, dep])


if __name__ == '__main__':
    client = xmlrpclib.ServerProxy('http://pypi.python.org/pypi')
    packages = client.list_packages()

    for i, package in enumerate(packages):
        extract_package(package, client, i)
        if i > 15:
            break
