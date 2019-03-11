import logging

import pytz
import requests

from ._scanner_consts import DOCS_TO_SKIP, PATHS_TO_SKIP
from .docinfo import DocumentInfo
from .parse_dirlist import parse_dir_listing

LOG = logging.getLogger(__name__)

BASE_URL = 'http://openhelsinki.hel.fi'
SERVER_TIMEZONE = pytz.timezone('EET')


def scan_dir(path, max_depth=0):
    return Scanner().scan_dir(path, max_depth)


class Scanner(object):
    def __init__(self, base_url=BASE_URL, server_timezone=SERVER_TIMEZONE,
                 min_filesize=500,
                 docs_to_skip=DOCS_TO_SKIP, paths_to_skip=PATHS_TO_SKIP):
        self.base_url = base_url
        self.tz = server_timezone
        self.min_filesize = min_filesize
        self.docs_to_skip = docs_to_skip
        self.paths_to_skip = paths_to_skip

    def scan_dir(self, path, max_depth=0):
        dir_listing_html = self.fetch_contents(path)
        for dir_entry in parse_dir_listing(dir_listing_html):
            if self._should_skip_dir_entry(dir_entry):
                continue

            if dir_entry.type == 'dir':
                if max_depth > 0:  # Recurse to the subdirectory
                    path = dir_entry.href
                    for doc_info in self.scan_dir(path, max_depth - 1):
                        yield doc_info
            else:
                try:
                    doc_info = DocumentInfo(dir_entry, self.base_url, self.tz)
                except ValueError:
                    LOG.debug("Skipping invalid filename: %s", dir_entry.href)
                    continue

                if self._should_skip_document(doc_info):
                    continue

                yield doc_info

    def fetch_contents(self, path):
        response = requests.get(self.base_url + path)
        if response.status_code != 200:
            raise IOError("Failed to fetch: {}".format(self.base_url + path))
        return response.content

    def _should_skip_dir_entry(self, dir_entry):
        if dir_entry.type == 'dir' and dir_entry.href.endswith('.zip/'):
            LOG.debug("Skipping directory ending with .zip: %s", dir_entry.href)
            return True
        elif dir_entry.type == 'dir':
            return False  # Other directories should be processed
        elif not dir_entry.href.endswith('.zip'):
            return True  # Skip non-zip files
        elif dir_entry.size < self.min_filesize:
            LOG.warn("File too small: %s %d", dir_entry.href, dir_entry.size)
            return True
        elif dir_entry.href in self.paths_to_skip:
            reason = self.paths_to_skip[dir_entry.href]
            LOG.info("Skipping document (%s): %s", reason, dir_entry.href)
            return True
        return False

    def _should_skip_document(self, doc_info):
        if doc_info.language != 'fi':
            # Skip non-Finnish documents (i.e. Swedish)
            return True
        if doc_info.origin_id in self.docs_to_skip:
            reason = self.docs_to_skip[doc_info.origin_id] or 'unknown reason'
            LOG.info("Skipping document (%s): %s", reason, doc_info.origin_id)
            return True
        return False
