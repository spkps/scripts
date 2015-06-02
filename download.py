#!/usr/bin/env python3

from pathlib import Path
from argparse import ArgumentParser
from urllib import request
from urllib.parse import urlparse

from bs4 import BeautifulSoup


EXUA_URL = 'http://www.ex.ua'


def retrieve_file(fileurl, filepath):
    if not isinstance(filepath, str):
        filepath = str(filepath)
    request.urlretrieve(fileurl, filepath)


def get_soup(exuaurl):
    f = request.urlopen(exuaurl)
    page = f.read().decode('utf-8')
    return BeautifulSoup(page)


def find_filelist_url_on_page(soup):
    lst = soup.find('table', class_='list')
    return lst.tr.a['href']


def find_files_on_page(soup):
    lst = soup.find('table', class_='list')
    smalls = lst.find_all('span', class_='small')
    for small in smalls:
        td = small.parent
        yield td.a['title'], td.a['href']


def read_filelist_with_url(filelisturl):
    f = request.urlopen(filelisturl)
    data = f.read().decode('utf-8')
    for line in data.split('\n'):
        if line:  # skip empty
            yield line


def gen_filename_from_url(url, extension=None):
    o = urlparse(url)
    path = o.path
    filename = path[path.rfind('/')+1:]
    if extension:
        filename = "{}.{}".format(filename, extension)
    return filename


def get_files_from_filelist(filelisturl, extension=None):
    for url in read_filelist_with_url(filelisturl):
        filename = gen_filename_from_url(url, extension)
        yield filename, url


def is_filelist_url(url):
    o = urlparse(url)
    path = o.path.strip('/')
    return path.startswith('filelist/')


def get_files(url, extension=None):
    filelist_reader = lambda: get_files_from_filelist(url, extension)
    page_reader = lambda: find_files_on_page(get_soup(url))
    reader = filelist_reader if is_filelist_url(url) else page_reader
    yield from reader()


def load_files_for_url(url, dst, extension=None):

    if not dst.exists():
        print("creating: {}".format(str(dst)))
        dst.mkdir()

    for filename, fileurl in get_files(url, extension):
        full_url = request.urljoin(EXUA_URL, fileurl)
        filepath = dst.joinpath(filename)
        print("downloading: {} -> {}".format(full_url, filepath))
        retrieve_file(full_url, filepath)


def create_arg_parser():
    parser = ArgumentParser()
    parser.add_argument('src', type=str,
                        help="ex.ua URL or path to the file "
                             "with direct URLs to download")

    parser.add_argument('dst', type=Path, help="A path to store the files")

    parser.add_argument('--ext', type=str, default=None,
                        help="Extension to add to file names from the list")

    return parser


def main():

    parser = create_arg_parser()
    args = parser.parse_args()
    load_files_for_url(args.src, args.dst, args.ext)


if __name__ == '__main__':
     main()
