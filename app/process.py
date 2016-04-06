from lxml.html import clean
import bbcode
import bleach
import bs4
import logging
import re


ATTRS = [
    'class',
    'data-page-document-table-col-width',
    'height',
    'href',
    'src',
    'style',
    'width',
]

TAGS = [
    'p', 'b', 'i', 'em', 'br', 'table', 'tr', 'td', 'tbody',
    'h2', 'h1', 'a', 'h3', 'ul', 'li', 'ol', 'img', 'u', 'hr',
    'sup', 'strong', 'span', 'style',
]


def process_html(html):
  logging.info(html)
  soup = bs4.BeautifulSoup(html, 'lxml')
  remove_comments(soup)
  tables = soup.findAll('table')
  for table in tables:
    if table.findParent('table') is None:
      tr = table.find('tr')
      if '[table=data' in str(tr):
        table['class'] = 'page-document-data-table'
      col_width = re.findall('\[table.*width=([^\]]*)\]', str(tr))
      if col_width:
        logging.info(table.attrs)
        table.attrs['data-page-document-table-col-width'] = col_width
        logging.info(table.attrs)
      if '[table' in str(tr):
        tr.extract()
  html = soup.body.prettify()
  html = bleach.clean(html,
      tags=TAGS,
      attributes=ATTRS,
      strip=True)
  cleaner = clean.Cleaner(style=True)
  html = cleaner.clean_html(html)
  html = markdownify(html)
  return html


def markdownify(html):
  html = re.sub('\_{2}(.+)\_{2}', '<i>\\1</i>', html, re.MULTILINE)
  html = re.sub('\*{2}(.+)\*{2}', '<strong>\\1</strong>', html, re.MULTILINE)
  html = re.sub('\[COLOR:([^\]]*)\]', '<div class="page-component-color" style="background-color:\\1"></div>', html, re.MULTILINE)
  html = html.replace('[TOC]', '<div class="toc toc--auto"><ul></ul></div>')
  html = re.sub('\[BUTTON:([^\]]*)\]([^\]]*)\[/\]', '<a class="btn" href="\\1">\\2</a>', html, re.MULTILINE)
  return html


def bbcodeify(html):
  parser = bbcode.Parser(
      escape_html=False,
      normalize_newlines=False,
      newline='')
#    parser.add_formatter('FOLDER', render_folder)
  return parser.format(html)


def remove_comments(soup):
  for el in soup.find_all('a'):
    if el.get('id') and el['id'].startswith('cmnt'):
      footer_parent = el.find_parent('div')
      if footer_parent:
        footer_parent.decompose()
      sup_parent = el.find_parent('sup')
      if sup_parent:
        sup_parent.decompose()
