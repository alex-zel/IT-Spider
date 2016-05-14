from distutils.core import setup
import py2exe
import sys
import os
import shutil
import glob

sys.argv.append('py2exe')


def find_data_files(source, target, patterns):
    """
    Locates the specified data-files and returns the matches
    in a data_files compatible format.
    :param source: source is the root of the source data tree.
                   Use '' or '.' for current directory.
    :param target: target is the root of the target data tree.
                   Use '' or '.' for the distribution directory.
    :param patterns: patterns is a sequence of glob-patterns for the
                    files you want to copy.
    :return:
    """
    if glob.has_magic(source) or glob.has_magic(target):
        raise ValueError("Magic not allowed in src, target")
    ret = {}
    for pattern in patterns:
        pattern = os.path.join(source, pattern)
        for filename in glob.glob(pattern):
            if os.path.isfile(filename):
                targetpath = os.path.join(target, os.path.relpath(filename, source))
                the_path = os.path.dirname(targetpath)
                ret.setdefault(the_path, []).append(filename)
    return sorted(ret.items())

if os.path.exists(r'./IT Spider'):
    shutil.rmtree(r'./IT Spider')

'''
data_files = []
for files in os.listdir('./img/'):
    f1 = './img/' + files
    if os.path.isfile(f1):  # skip directories
        f2 = 'img', [f1]
        data_files.append(f2)
'''

setup(windows=[{"script": "IT Spider.py", "icon_resources": [(0, "./img\\tachk.ico")]}],
      data_files=find_data_files('', '', ['data/*', 'img/*', 'lib\*']),
      options={'py2exe': {'packages': ["pywinauto"],
                          'bundle_files': 2,
                          'compressed': True,
                          'dist_dir': './IT Spider'}},
      zipfile=None,)
