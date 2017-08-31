"""
Cache for frequently needed information. This persists to disk if we can, and
otherwise is an in-memory cache.
"""

import contextlib
import os
import sqlite3
import threading

import stem.util.log

import nyx

CACHE = None
CACHE_LOCK = threading.RLock()

SCHEMA_VERSION = 1  # version of our scheme, bump this if you change the following
SCHEMA = (
  'CREATE TABLE schema(version NUMBER)',
  'INSERT INTO schema(version) VALUES (%i)' % SCHEMA_VERSION,

  'CREATE TABLE relays(fingerprint TEXT PRIMARY KEY, address TEXT, or_port NUMBER, nickname TEXT)',
)


@contextlib.contextmanager
def cache():
  """
  Provides the sqlite cache for application data.

  :returns: :class:`~nyx.cache.Cache` for our applicaion
  """

  global CACHE

  with CACHE_LOCK:
    if CACHE is None:
      CACHE = Cache()

    yield CACHE


class Cache(object):
  """
  Cache for frequently used information.
  """

  def __init__(self):
    cache_path = nyx.data_directory('cache.sqlite')

    if cache_path:
      try:
        self._conn = sqlite3.connect(cache_path)
        schema = self._conn.execute('SELECT version FROM schema').fetchone()[0]
      except:
        schema = 'no schema'

      if schema != SCHEMA_VERSION:
        stem.util.log.info('Cache schema of %s is out of date (has %s but current version is %s). Clearing the cache.' % (cache_path, schema, SCHEMA_VERSION))

        self._conn.close()
        os.remove(cache_path)
        self._conn = sqlite3.connect(cache_path)

        for cmd in SCHEMA:
          self._conn.execute(cmd)
    else:
      self._conn = sqlite3.connect(':memory:')

      for cmd in SCHEMA:
        self._conn.execute(cmd)

  def query(self, query, *param):
    """
    Performs a query on our cache.
    """

    return self._conn.execute(query, param)
