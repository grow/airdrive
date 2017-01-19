from google.appengine.api import search

INDEX = 'pages'


def create_doc(page):
    doc_id = page.resource_id
    lang = 'en'
    folders = [str(key.id()) for key in page.parents]
    folders = ' '.join(folders)
    fields = [
        search.HtmlField(name='html', value=page.processed_html, language=lang),
        search.TextField(name='title', value=page.title, language=lang),
        search.TextField(name='folders', value=folders),
    ]
    doc = search.Document(doc_id=doc_id, fields=fields)
    return doc


def index_doc(page, index=INDEX):
    doc = create_doc(page)
    index = search.Index(INDEX)
    index.put(doc)


def do_search(q, index=INDEX):
    snippeted_fields = ['html']
    options = search.QueryOptions(snippeted_fields=snippeted_fields)
    query = search.Query(q, options=options)
    index = search.Index(INDEX)
    return index.search(query)


def to_messages(results):
    message_results = []
    return message_results
