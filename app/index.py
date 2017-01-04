from google.appengine.api import search

INDEX = 'pages'


def create_doc(page):
    doc_id = page.resource_id
    lang = 'en'
    fields = [
        search.HtmlField(name='html', value=page.processed_html, language=lang),
        search.TextField(name='title', value=page.title, language=lang),
    ]
    doc = search.Document(doc_id=doc_id, fields=fields)
    return doc


def index_doc(page, index=INDEX):
    doc = create_doc(page)
    index = search.Index(INDEX)
    index.put(doc)


def do_search(q, index=INDEX):
    query = search.Query(q)
    index = search.Index(INDEX)
    return index.search(query)
