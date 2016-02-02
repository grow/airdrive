from markdown.extensions import tables
from markdown.extensions import toc
import markdown


def do_markdown(value):
  extensions = [
      tables.TableExtension(),
      toc.TocExtension(),
  ]
  return markdown.markdown(value, extensions=extensions)


def do_filesizeformat(value, binary=False):
  bytes = float(value)
  base = binary and 1024 or 1000
  prefixes = [
    (binary and 'KiB' or 'kB'),
    (binary and 'MiB' or 'MB'),
    (binary and 'GiB' or 'GB'),
    (binary and 'TiB' or 'TB'),
    (binary and 'PiB' or 'PB'),
    (binary and 'EiB' or 'EB'),
    (binary and 'ZiB' or 'ZB'),
    (binary and 'YiB' or 'YB')
  ]
  if bytes == 1:
    return '1 Byte'
  elif bytes < base:
    return '%d Bytes' % bytes
  else:
    for i, prefix in enumerate(prefixes):
      unit = base ** (i + 2)
      if bytes < unit:
        return '%.1f %s' % ((base * bytes / unit), prefix)
    return '%.1f %s' % ((base * bytes / unit), prefix)
