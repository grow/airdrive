from lxml.html import clean
import bs4
import cssutils
import logging
import re
import urllib

cssutils.log.setLevel(logging.CRITICAL)


ATTRS = [
    'class',
    'data-page-document-table--has-images',
    'data-page-document-table-col-width',
    'data-page-document-table-size',
    'height',
    'href',
    'src',
    'start',
    'style',
    'width',
]

ALLOWED_CLASSES = [
    'text--highlight',
]

EMPTY_TAGS_TO_REMOVE = [
    'a',
    'h1',
    'h2',
    'h3',
    'h4',
    'h5',
    'h6',
    'p',
    'span',
    'table',
    'tbody',
]

ALL = re.MULTILINE|re.DOTALL


def process_html(html):
  if not html:  # None, empty string handling.
      return html

  soup = bs4.BeautifulSoup(html, 'lxml')
  style_tag = soup.find('style')

  class_matches = re.findall(r'(c\d{1,2})(\{(.*?)\})', unicode(style_tag))
  highlight_classes_to_colors = find_original_highlight_classes(
      style_tag, 'background-color', class_matches)
  for class_name, color in highlight_classes_to_colors.iteritems():
      replace_class_with_tag(
          soup, [class_name], 'span', class_name='text--highlight',
          background_color=color)
  bold_classes = find_original_classes(style_tag, 'font-weight:bold',
      class_matches)
  bold_italic_classes = find_original_classes(style_tag,
      'font-weight:bold.*font-style:italic', class_matches)
  bold_italic_classes += find_original_classes(style_tag,
      'font-style:italic.*font-weight:bold', class_matches)
  italic_classes = find_original_classes(style_tag, 'font-style:italic',
      class_matches)
  center_classes = find_original_classes(style_tag, 'text-align:center',
      class_matches)

  replace_class_with_tag(soup, bold_italic_classes, 'span',
                         class_name='text--bold-and-italic')
  replace_class_with_tag(soup, italic_classes, 'em')
  replace_class_with_tag(soup, bold_classes, 'strong')
  replace_css_class(soup, 'p', center_classes, 'text--centered')
  style_text = style_tag.text
  remove_comments(soup)
  fix_image_sizes(soup)
  process_tables(soup, style_text)
  process_hrefs(soup)
  remove_styles(soup)
  if soup:
      remove_empty_tags(soup, EMPTY_TAGS_TO_REMOVE)
  html = soup.body.prettify()
  html = process_special_tags(html)
  return html


def process_special_tags(html):
  html = re.sub('\[caption\|check\]([^\[]*)\[/caption\]', '<div class="caption caption--check"><div class="caption-bar"></div><div class="caption-label">Check</div><div class="caption-text">\\1</div></div>', html, ALL)
  html = re.sub('[^`]\[caption\]([^\[]*)\[/caption\]', '<div class="caption"><div class="caption-text">\\1</div></div>', html, ALL)
  html = re.sub('[^`]\[caption\](.*)\[/caption\]', '<div class="caption"><div class="caption-text">\\1</div></div>', html, ALL)
  html = re.sub('(?:[^`]?)\[bar\]([^\[]+)\[/bar\]', '<div class="layout-main-bar"><div class="layout-main-bar-content">\\1</div></div>', html, ALL)
  html = re.sub('[^`]\[caption\|dont\]([^\[]*)\[/caption\]', '<div class="caption caption--dont"><div class="caption-bar"></div><div class="caption-label">Don\'t</div><div class="caption-text">\\1</div></div>', html, ALL)
  html = re.sub('[^`]\[caption\|dont\]\[/caption\]', '<div class="caption caption--dont"><div class="caption-bar"></div><div class="caption-label">Don\'t</div><div class="caption-text"></div></div>', html, ALL)
  html = re.sub('[^`]\[caption\|do\]([^\[]*)\[/caption\]', '<div class="caption caption--do"><div class="caption-bar"></div><div class="caption-label">Do</div><div class="caption-text">\\1</div></div>', html, ALL)
  html = re.sub('[^`]\[caption\|label\]([^\[]*)\[/caption\]', '<div class="caption"><div class="caption-label">\\1</div></div>', html, ALL)
  html = re.sub('\[fullwidthimage\|([^\]]*)\]', '<div class="page-image-container page-image-container--fullwidth"><img src="\\1"></div>', html, ALL)
  html = re.sub('[^`]\[toc\]', '<div class="toc toc--auto"><ul></ul></div>', html)
  html = re.sub('[^`]\[TOC\]', '<div class="toc toc--auto"><ul></ul></div>', html)
  html = re.sub('[^`]\[hr\]', '<hr>', html)
  html = re.sub('\[link\|([^\]]*)\]([^\[]+)\[/link\]', '<a href="\\1">\\2</a>', html)
  html = re.sub('\[spacer\|([^\]]*)\]', '<div style="height: \\1"></div>', html)
  html = re.sub('[^`]\[b\]([^\[]+)\[/b\]', '<strong>\\1</strong>', html)
  html = re.sub('[^`]\[i\](.*)\[/i\]', '<em>\\1</em>', html)
  html = re.sub('\[colorize\|([^\]]+)\]([^\[]+)\[/colorize\]', '<span style="color: \\1">\\2</span>', html, ALL)
  html = re.sub('(?:[^`]?)\[bi\](.*)\[/bi\]', '<strong><em>\\1</em></strong>', html)
  html = re.sub('(?:[^`]?)\[h2\]([^\[]+)\[/h2\]', '<h2>\\1</h2>', html, ALL)
  html = re.sub('(?:[^`]?)\[h1\]([^\[]+)\[/h1\]', '<h1>\\1</h1>', html, ALL)
  html = re.sub('(?:[^`]?)\[h2\|tout\]([^\[]+)\[/h2\]', '<h2 class="tout-wrap"><span class="tout tout--mid"><span class="tout__content">\\1</span></span></h2>', html, ALL)
  html = re.sub('(?:[^`]?)\[tout\|right\]([^\[]+)\[/tout\]', '<div class="tout-wrap"><span class="tout tout--large tout--large-pulled tout--right"><span class="tout__content">\\1</span></span></div>', html, ALL)
  html = re.sub('(?:[^`]?)\[tout\|center\]([^\[]+)\[/tout\]', '<div class="tout-wrap"><span class="tout tout--mid tout--centered"><span class="tout__content">\\1</span></span></div>', html, ALL)
  html = re.sub('(?:[^`]?)\[tout\|center\|color\|([^\]]+)\]([^\[]+)\[/tout\]', '<div class="tout-wrap"><span class="tout tout--mid tout--centered" style="background-color: \\1"><span class="tout__content">\\2</span></span></div>', html, ALL)
  html = re.sub('(?:[^`]?)\[tout\|mid\|color\|([^\]]+)\]([^\[]+)\[/tout\]', '<div class="tout-wrap"><span class="tout tout--mid" style="background-color: \\1"><span class="tout__content">\\2</span></span></div>', html, ALL)
  html = re.sub('(?:[^`]?)\[tout\|mid\]([^\[]+)\[/tout\]', '<div class="tout-wrap"><span class="tout tout--mid"><span class="tout__content">\\1</span></span></div>', html, ALL)
  html = re.sub('(?:[^`]?)\[tout\|top\]([^\[]+)\[/tout\]', '<div class="tout-wrap"><span class="tout tout--mid tout--mid-pulled"><span class="tout__content">\\1</span></span></div>', html, ALL)
  html = re.sub('(?:[^`]?)\[tout\|top\|color\|([^\]]+)\]([^\[]+)\[/tout\]', '<div class="tout-wrap"><span class="tout tout--mid tout--mid-pulled" style="background-color: \\1"><span class="tout__content">\\2</span></span></div>', html, ALL)
  html = re.sub('(?:[^`]?)\[h2\]([^\[]+)\[/h2\]', '<h2>\\1</h2>', html, ALL)
  html = re.sub('(?:[^`]?)\[h2\|center\]([^\[]+)\[/h2\]', '<h2 class="text--centered">\\1</h2>', html, ALL)
  html = re.sub('(?:[^`]?)\[h3\|center\]([^\[]+)\[/h3\]', '<h3 class="text--centered">\\1</h3>', html, ALL)
  # html = re.sub('(?:[^`]?)\[h3\]([^\[]+)\[/h3\]', '<h3>\\1</h3>', html, all)
  html = re.sub('\[h4\]([^\[]+)\[/h4\]', '<h4>\\1</h4>', html, ALL)
  html = re.sub('\[h3\]([^\[]+)\[/h3\]', '<h3>\\1</h3>', html, ALL)
  html = re.sub('(?:[^`]?)\[h5\|color:([^\[]+)\]([^\[]+)\[/h5\]', '<h5 style="color: \\1">\\2</h5>', html, ALL)
  html = re.sub('\[h5\]([^\[]+)\[/h5\]', '<h5>\\1</h5>', html, ALL)
  html = re.sub('(?:[^`]?)\[h4\]([^\[]+)\[/h4\]', '<h4>\\1</h4>', html, ALL)
  html = re.sub('(?:[^`]?)\[h5\]([^\[]+)\[/h5\]', '<h5>\\1</h5>', html, ALL)
  html = re.sub('\[intro\]([^\[]+)\[/intro\]', '<div class="page-intro">\\1</div>', html, ALL)
  html = re.sub('\[button\|([^\]]*)\]([^\[]*)\[/button\]', '{% with page = get_page("\\1") %}<a class="btn" href="{{page.url}}">\\2</a>{% endwith %}', html, ALL)
  html = re.sub('\[button\]([^\[]*)\[/button\]', '<a class="btn">\\1</a>', html, ALL)
  # [color|rgb:223,51,42|cmyk:7,94,97,1|hex:#df332a|pantone:179c]
  html = re.sub('[^`]\[color\|rgb:(.*)\|cmyk:(.*)\|hex:(.*)\|pantone:(.*)\](.*)\[/color\]', '<div class="color-chip"><div class="color-chip-color" style="background-color:\\3"></div><div class="color-chip-name">\\5</div><div class="color-chip-colors"><div class="color-chip-colors-color"><span>rgb</span>\\1</div><div class="color-chip-colors-color"><span>cmyk</span>\\2</div><div class="color-chip-colors-color"><span>hex</span>\\3</div><div class="color-chip-colors-color"><span>pantone</span>\\4</div></div></div>', html, ALL)
  html = re.sub('[^`]\[color\|rgb:(.*)\|cmyk:(.*)\|hex:(.*)\](.*)\[/color\]', '<div class="color-chip"><div class="color-chip-color" style="background-color:\\3"></div><div class="color-chip-name">\\4</div><div class="color-chip-colors"><div class="color-chip-colors-color"><span>rgb</span>\\1</div><div class="color-chip-colors-color"><span>cmyk</span>\\2</div><div class="color-chip-colors-color"><span>hex</span>\\3</div></div></div>', html, ALL)
  html = re.sub('[^`]\[color.*\](.*)\[/color\]', '<div class="color-chip"><div class="color-chip-color"></div><div class="color-chip-name">\\1</div></div>', html, ALL)
  html = re.sub('\[download\|([^\]]*)\]([^\[]*)\[caption\]([^\[]*)\[/download\]', '<div class="page-info"><div class="page-info-icon"><i class="material-icons">file_download</i></div><div class="page-info-content"><a href="\\1" class="page-info-content-label">\\2</a><div class="page-info-content-filesize">\\3</div><div class="page-info-content-filesize"></div></div></div>', html, ALL)
  html = re.sub('\[info\|([^\]]*)\]([^\[]*)\[caption\]([^\[]*)\[/info\]', '<a class="page-info" href="\\1"><span class="page-info-icon"><i class="material-icons">info</i></span><span class="page-info-content"><span class="page-info-content-label">\\2</span><span class="page-info-content-filesize">\\3</span></span></a>', html, ALL)
  html = re.sub('\[highlight\|([^\]]*)\]([^\[]*)\[/highlight\]', '<span class="highlight" style="background-color:\\1">\\2</span>', html, ALL)
  html = re.sub('\[info\|([^\]]*)\]([^\[]*)\[/info\]', '<a class="page-info" href="\\1"><span class="page-info-icon"><i class="material-icons">info</i></span><span class="page-info-content"><span class="page-info-content-label">\\2</span></span></a>', html, ALL)
  html = re.sub('\[info\]([^\[]*)\[caption\]([^\[]*)\[/info\]', '<div class="page-info"><div class="page-info-icon"><i class="material-icons">info</i></div><div class="page-info-content"><div class="page-info-content-label">\\1</div><div class="page-info-content-filesize">\\2</div></div></div>', html, ALL)
  html = re.sub('\[info\](.*)\[/info\]', '<div class="page-info"><div class="page-info-icon"><i class="material-icons">info</i></div><div class="page-info-content"><div class="page-info-content-filesize">\\1</div></div></div>', html, ALL)
  html = re.sub('\[download\|([^\]]*)\](.*)\[/download\]', '{% with asset = get_asset("\\1") %}<div class="page-info"><div class="page-info-icon"><i class="material-icons">file_download</i></div><div class="page-info-content"><a {% if asset %}href="{{asset.download_url}}" data-g-event="Download" data-g-action="link" data-g-label="{{asset.title}}"{% endif %} class="page-info-content-label">\\2</a><div class="page-info-content-filesize">{{asset.size|filesizeformat if asset else "Unavailable"}}</div></div></div>{% endwith %}', html, ALL)
  html = re.sub('\[page\|(.*)#(.*)\](.*)\[/page\]', '{% with page = get_page("\\1") or get_folder("\\1") %}<a href="{{page.url}}#\\2">\\3</a>{% endwith %}', html, ALL)
  html = re.sub('\[video]([^\[]*)\[/video\]', '{% with asset = get_asset("\\1") %}{% include "tags/video.html" with context %}{% endwith %}', html, ALL)
  html = re.sub('\[page\|([^\]]*)\]([^\[]*)\[/page\]', '{% with page = get_page("\\1") or get_folder("\\1") %}<a href="{{page.url}}">\\2</a>{% endwith %}', html, ALL)
  html = re.sub('\[next\|([^\]]*)\]([^\[]*)\[/next\]', '{% with page = get_page("\\1") or get_folder("\\1") %}{% set caption %}{% filter striptags %}\\2{% endfilter %}{% endset %}{% include "_nav_bar.html" with context %}{% endwith %}', html, ALL)
  html = re.sub('\[callout\|(.*)#(.*)\|([^\]]*)\]([^\[]*)\[/callout\]', '{% with page = get_page("\\1") or get_folder("\\1") %}{% with bookmark = "\\2" %}{% with url = "\\3" %}{% set caption %}{% filter striptags %}\\4{% endfilter %}{% endset %}{% include "_callout.html" with context %}{% endwith %}{% endwith %}{% endwith %}', html, ALL)
  html = re.sub('\[callout\|([^\|]*)\|([^\]]*)\]([^\[]*)\[/callout\]', '{% with page = get_page("\\1") or get_folder("\\1") %}{% with url = "\\2" %}{% set caption %}{% filter striptags %}\\3{% endfilter %}{% endset %}{% include "_callout.html" with context %}{% endwith %}{% endwith %}', html, ALL)
  html = re.sub('[^`]\[youtube\](.*)\[/youtube\]', '<div class="page-youtube-video"><iframe width="560" height="315" src="https://www.youtube.com/embed/\\1" frameborder="0" allowfullscreen></iframe></div>', html, ALL)
  html = re.sub('\[download\](.*)\[/download\]', '<div class="page-info"><div class="page-info-icon"><i class="material-icons">file_download</i></div><div class="page-info-content"><div class="page-info-content-label">\\1</div><div class="page-info-content-filesize">100 KB</div></div></div>', html, ALL)
  html = re.sub('\[assets\]([^\[]*)\[/assets\]', '<div class="page-info" data-asset-parentKey="\\1"><div class="page-info-icon"><i class="material-icons">file_download</i></div><div class="page-info-content"><a class="page-info-content-label">Download</a><div class="page-info-content-filesize"></div></div></div>', html, ALL)
  html = re.sub('\[singlecolumnimage\|([^\]]*)\]', '<div class="page-image-container page-image-container--singlecolumn"><div class="page-image" style="background-image:url(\\1)"></div></div>', html)
  html = re.sub('\[heroimage\|([^\]]*)\]', '<div class="page-image-container page-image-container--hero"><img class="page-image--hero" src="\\1"></div>', html)
  html = re.sub('\[bgimage\|([^\]]*)\]', '<div class="page-image-container page-image-container--bg"><div class="page-image page-image--bg" style="background-image: url(\\1)"></div></div>', html)
  html = re.sub('\[slides\|([^\]]*)\]', '<iframe class"frame-slides" frameborder="0" src="https://docs.google.com/presentation/d/\\1/embed?authuser=0" allowfullscreen></iframe>', html)
  html = re.sub('\[fullsizeimage\|(.*)\]', '<div class="page-image-container page-image-container--fullsize"><div class="page-image" style="background-image:url(\\1)"></div></div>', html, ALL)
  html = re.sub('\[thumbnails\|([^\]]*)\]', '{% with folder = get_folder("\\1") %}{% import "_macros.html" as macros with context %}{{macros.render_assets(folder.children[\'assets\'], folder=folder)}}{% endwith %}', html, ALL)
  html = re.sub('\[fullwidthimage\|([^\]]*)\]', '<div class="page-image-container page-image-container--fullwidth"><img src="\\1"></div>', html, ALL)
  html = re.sub('\`([^`]*)\`', '<code>\\1</code>', html)
  html = re.sub('</ol>[^<]*<ol>', '', html, ALL)
  html = re.sub('\[nav\|next([^\]]*)\]', '{% with page = get_page("\\1") %}{% include "nav.html" with context %}{% endwith %}', html, ALL)
  return html


def remove_comments(soup):
  for el in soup.find_all('a'):
    ident = el.get('id')
    if ident and ident.startswith(('cmnt', 'ftnt')):
      footer_parent = el.find_parent('div')
      if footer_parent:
        footer_parent.decompose()
      sup_parent = el.find_parent('sup')
      if sup_parent:
        sup_parent.decompose()


def remove_empty_tags(soup, tag_names):
  for tag_name in tag_names:
    for element in soup.find_all(tag_name):
      if not element or element.find_all('img'):
        continue
      text = element.get_text().strip()
      if dict(element.attrs).get('class') in ALLOWED_CLASSES:
        continue
      elif not text or not len(text):
        element.decompose()
      elif tag_name == 'span' and not element.findAll(True):
        element.unwrap()
      elif tag_name == 'p':
        if re.search('\[tout', text):
          element.unwrap()
        if (re.search('[^`]\[h\d\]', text)
            or re.search('^\[h\d\]', text)) and element.find('span'):
          element.find('span').unwrap()
          element.unwrap()


def find_original_highlight_classes(style_tag, search_str, class_matches):
  highlight_classes_to_colors = {}
  background_color = None
  if class_matches:
    for match in class_matches:
      if re.search(search_str, match[1], ALL):
        style = cssutils.parseStyle(match[1][1:-1])
        background_color = style.backgroundColor
        highlight_classes_to_colors[match[0]] = background_color
  return highlight_classes_to_colors


def find_original_classes(style_tag, search_str, class_matches):
  classes = []
  if class_matches:
    for match in class_matches:
      if re.search(search_str, match[1], ALL):
        classes.append(match[0])
  return classes


def replace_class_with_tag(soup, css_classes, tagname,
      class_name=None, background_color=None):
  for css_class in css_classes:
    for element in soup.find_all('span', class_=css_class):
      element_text = element.get_text()
      if (len(element_text) == 0
          or element.find_parent('h2')
          or element.find_parent('h3')):
        continue
      replacement_tag = soup.new_tag(tagname)
      replacement_tag.string = element_text
      if background_color != '#fff':
        if class_name:
          replacement_tag['class'] = class_name
        if background_color:
          replacement_tag['style'] = (
              'background-color: {}'.format(background_color))
      element.replace_with(replacement_tag)


def replace_css_class(soup, tagname, from_css_classes, to_css_class):
  for css_class in from_css_classes:
    for element in soup.find_all(tagname, class_=css_class):
      element['class'] = to_css_class


def fix_image_sizes(soup):
  for img in soup.find_all('img'):
    css = img.get('style')
    style = cssutils.parseStyle(css)
    if style.width:
      img['width'] = style.width.replace('px', '')
    if style.height:
      img['height'] = style.height.replace('px', '')


def remove_styles(soup):
  for tag in soup.findAll(True):
    if tag.attrs:
      if 'class' in tag and tag['class'] not in ALLOWED_CLASSES:
        tag.attrs.pop('class', None)


def process_tables(soup, style_tag):
  sheet = cssutils.parseString(style_tag)

  # Map drive classes to style rules.
  drive_classes_to_rules = {}
  style_rules = sheet.cssRules.rulesOfType(cssutils.css.CSSRule.STYLE_RULE)
  for rule in style_rules:
    if rule.selectorText.startswith('.c'):
      drive_classes_to_rules[rule.selectorText] = rule

  for table in soup.find_all('table'):
    save_widths = False

    # Process special image tags in all cells.
    for cell in table.find_all('td'):
      cell_str = str(cell)
      process_image_tag('fullwidthimage', table, cell, cell_str)
      process_image_tag('bgimage', table, cell, cell_str)
      process_image_tag('heroimage', table, cell, cell_str)
      process_image_tag('singlecolumnimage', table, cell, cell_str,
          attr='data-page-document-table--has-images')
      process_callout_image('callout', table, cell, cell_str)

    # Process table header.
    first_row = table.find('tr')
    extracted_first_row = False
    if not first_row.find('table'):
      tr_str = str(first_row)
      if 'class' not in table:
        table['class'] = ''
      if re.findall('\[table.*brand', tr_str):
        table['class'] += 'page-document-table page-document-table--brand'
      if re.findall('\[table.*colored', tr_str):
        table['class'] += 'page-document-table page-document-table--colored'
      if re.findall('\[table.*callout', tr_str):
        table['class'] += 'page-document-table page-document-table--callout'
      if re.findall('\[table.*data', tr_str):
        table['class'] += ' page-document-table--data'
      if re.findall('table.*glossary', tr_str):
        table['class'] += ' page-document-table--glossary'
      if re.findall('table.*savewidths', tr_str):
        save_widths = True
        table['class'] += ' page-document-table--save-widths'
      if re.findall('\[table.*bg]', tr_str):
        table['class'] += ' page-document-table--bg'
      if re.findall('\[table.*noheader', tr_str):
        table['class'] += ' page-document-table--no-header'
      is_fixed = re.findall('\[table.*fixed\]', tr_str)
      if is_fixed:
        table['class'] += ' page-document-table--fixed'
      col_width = re.findall('\[table.*width=([^\]]*)\]', tr_str)
      if col_width:
        table.attrs['data-page-document-table-col-width'] = col_width
      if '[table' in tr_str:
        extracted_first_row = True
        first_row.extract()

    # Get a new first row.
    if extracted_first_row:
      first_row = table.find('tr')
    columns = first_row.find_all('td', recursive=False)
    widths = []
    for cell in columns:
      class_names = cell.get('class') or []
      for class_name in class_names:
        class_name = '.{}'.format(class_name)
        if class_name in drive_classes_to_rules:
          rule = drive_classes_to_rules[class_name]
          width = rule.style.width
          widths.append(width)

    # Only compare widths for 1/3 column layouts.
    if len(widths) == 2:
      width_left = widths[0].replace('pt', '') or '0'
      width_right = widths[1].replace('pt', '') or '0'
      if float(width_left) < float(width_right):
        table.attrs['data-page-document-table-size'] = '2-col-wide'

    if save_widths:
      total = 0
      for width in widths:
        total += float(width.replace('pt', '') or '0')
      main_cols = table.find('tr').find_all('td', recursive=False)
      for i, col in enumerate(main_cols):
        width = float(widths[i].replace('pt', '') or 0) / total
        col['style'] = 'width: {}%'.format(width * 100)


def process_hrefs(soup):
  for a in soup.find_all('a'):
    if a.attrs.get('href'):
      a['href'] = clean_google_href(a['href'])


def clean_google_href(href):
  regex = ('^'
           + re.escape('https://www.google.com/url?q=')
           + '(.*?)'
           + re.escape('&'))
  match = re.match(regex, href)
  if match:
    encoded_url = match.group(1)
    return urllib.unquote(encoded_url)
  return href


def process_callout_image(name, table, cell, cell_str, attr=None):
  # [callout|id]Caption[/callout]
  regex = '.*\[callout\|([^\]]*)\]([^\[]*)\[/callout\].*'
  match = re.match(regex, cell_str)
  if match:
    groups = match.groups()
    if attr:
      table.attrs[attr] = 'true'
    img = cell.find('img')
    if img:
      url = img.get('src')
      img.decompose()
      cell.string = '[callout|{id}|{url}]{caption}[/callout]'.format(
          id=groups[0], url=url, caption=groups[1])


def process_image_tag(name, table, cell, cell_str, attr=None):
  if re.search(r'[^`]\[{}\]'.format(name), cell_str):
    if attr:
      table.attrs[attr] = 'true'
    img = cell.find('img')
    if img:
      url = img.get('src')
      for node in cell.find_all('p'):
        if '[{}]'.format(name) in str(node):
          node.string = '[{}|{}]'.format(name, url)
        img.decompose()
        node.unwrap()


def process_image_size_tag(table, cell, cell_str, attr=None):
  if re.search(r'[^`]\[imagesize|.*\]', cell_str):
    if attr:
      table.attrs[attr] = 'true'
    img = cell.find('img')
    if img:
      url = img.get('src')
      for node in cell.find_all('p'):
        match = re.match(r'\[imagesize|([^\]]+)\]', str(node))
        if match:
          size = match.groups()[0]
          node.string = '[imagesize|{}|{}]'.format(size, url)
        img.decompose()
        node.unwrap()
