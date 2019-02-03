import contextlib
import datetime
import io
import os
import sqlite3
from urllib import parse
from xml.sax import saxutils

from flask import (
    Flask,
    Response,
    abort,
    g,
    render_template,
    url_for,
)
import markdown


FEED_ID = "tag:talideon.com,2001:weblog"


app = Flask(__name__)


def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db_path = os.environ.get('LINKLOG_DB_PATH', 'db.sqlite')
        db = g._database = sqlite3.connect(db_path)
        db.row_factory = sqlite3.Row
    return db


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


class XMLBuilder:
    """
    XML document builder. The code is purposely namespace ignorant: it's up to
    user to supply appropriate `xmlns` attributes as needed.

    >>> xml = XMLBuilder()
    >>> with xml.within('root', xmlns='tag:talideon.com,2013:test'):
    ...     xml += 'Before'
    ...     with xml.within('leaf'):
    ...         xml += 'Within'
    ...     xml += 'After'
    ...     xml.tag('leaf', 'Another')
    >>> print xml.as_string()
    <?xml version="1.0" encoding="utf-8"?>
    <root xmlns="tag:talideon.com,2013:test">Before<leaf>Within</leaf>After<leaf>Another</leaf></root>
    """

    def __init__(self, out=None, encoding="utf-8"):
        """
        `out` should be a file-like object to write the document to. If none
        is provided, a buffer is created.

        Note that if you provide your own, `as_string()` will return `None`
        as no other sensible value can be returned.
        """
        if out is None:
            self.buffer = io.StringIO()
            out = self.buffer
        else:
            self.buffer = None
        self.generator = saxutils.XMLGenerator(out, encoding)
        self.generator.startDocument()

    @contextlib.contextmanager
    def within(self, tag, **attrs):
        """
        Generates an element containing nested elements.
        """
        self.generator.startElement(tag, attrs)
        yield
        self.generator.endElement(tag)

    def tag(self, tag, *values, **attrs):
        """
        Generates a simple element.
        """
        self.generator.startElement(tag, attrs)
        for value in values:
            self.generator.characters(value)
        self.generator.endElement(tag)

    def __getattr__(self, tag):
        return lambda *values, **attrs: self.tag(tag, *values, **attrs)

    def append(self, other):
        """
        Append the string to this document.
        """
        self.generator.characters(other)
        return self

    def as_string(self):
        """
        If using the built-in buffer, get its current contents.
        """
        if self.buffer is None:
            return None
        return self.buffer.getvalue()

    def close(self):
        """
        If using the built-in buffer, clean it up.
        """
        if self.buffer is not None:
            self.buffer.close()
            self.buffer = None

    # Shortcuts.
    __iadd__ = append
    __str__ = as_string


def query(sql, args=()):
    con = get_db()
    cur = con.cursor()
    try:
        cur.execute(sql, args)
        for row in iter(cur.fetchone, None):
            yield row
    finally:
        cur.close()


def query_row(sql, args=(), default=None):
    con = get_db()
    cur = con.cursor()
    try:
        cur.execute(sql, args)
        for row in iter(cur.fetchone, None):
            return row
    finally:
        cur.close()
    return default


def query_value(sql, args=(), default=None):
    con = get_db()
    cur = con.cursor()
    try:
        cur.execute(sql, args)
        for row in iter(cur.fetchone, None):
            return row[0]
    finally:
        cur.close()
    return default


@app.route("/")
def latest():
    sql = """
        SELECT   id, time_c, time_m, link, title, via, note
        FROM     links
        ORDER BY time_c DESC
        LIMIT    40
        """
    return render_template("latest.html", entries=query(sql))


@app.route("/add")
def add_entry():
    return "Hello World!"


@app.route("/feed")
def feed():
    modified = query_value("SELECT MAX(time_m) FROM links")
    if modified:
        modified = parse_dt(modified)
        # TODO: ETag

    sql = """
        SELECT   id, time_c, time_m, link, title, via, note
        FROM     links
        ORDER BY time_m DESC
        LIMIT    40
        """

    xml = XMLBuilder()
    with xml.within('feed', xmlns='http://www.w3.org/2005/Atom'):
        xml.title('Inklings')
        xml.subtitle('A stream of random things')
        if modified:
            xml.modified(modified.isoformat())
        with xml.within('author'):
            xml.name('Keith Gaughan')
        xml.id(FEED_ID)
        xml.rights('Copyright (c) Keith Gaughan 2001-2019')
        xml.link(rel='alternate', type='text/html', hreflang='en',
                 href=url_for('latest', _external=True))
        xml.link(rel='self', type='text/html', hreflang='en',
                 href=url_for('feed', _external=True))

        for entry in query(sql):
            with xml.within('entry'):
                xml.title(entry['title'])
                xml.published(parse_dt(entry['time_c']).isoformat())
                xml.updated(parse_dt(entry['time_m']).isoformat())
                xml.id("{}:{}".format(FEED_ID, entry['id']))
                permalink = url_for('entry',
                                    entry_id=entry['id'],
                                    _external=True)
                alternate = entry['link'] if entry['link'] else permalink
                xml.link(rel='alternate', type='text/html', href=alternate)
                if entry['link']:
                    xml.link(rel='related',
                             type='text/html',
                             href=permalink)
                if entry['via']:
                    xml.link(rel='via', type='text/html', href=entry['via'])
                if entry['note']:
                    attrs = {
                        "type": "html",
                        "xml:lang": "en",
                        "xml:base": permalink,
                    }
                    xml.content(entry['note'], **attrs)

    return Response(xml.as_string(),
                    content_type='application/atom+xml; charset=UTF-8')


@app.route("/<string(length=4):year>-<string(length=2):month>")
def archive(year, month):
    dt = datetime.date(int(year), int(month), 1)
    sql = """
        SELECT  id, time_c, time_m, link, title, via, note
        FROM    links
        WHERE   time_c BETWEEN ? AND DATE(?, '+1 month')
        ORDER BY time_c ASC
        """
    entries = list(query(sql, (dt.isoformat(), dt.isoformat())))
    if not entries:
        abort(404)
    return render_template("month.html", entries=entries, dt=dt)


@app.route("/<int:entry_id>")
def entry(entry_id):
    sql = """
        SELECT   id, time_c, time_m, link, title, via, note
        FROM     links
        WHERE    id = ?
        """
    entry = query_row(sql, (entry_id,))
    if entry is None:
        abort(404)
    return render_template("entry.html", entry=entry)


@app.route("/<int:entry_id>;edit")
def edit_entry(entry_id):
    return ""


@app.template_filter('markdown')
def md(text):
    return markdown.markdown(text,
                             output_format='html',
                             extensions=['smarty',
                                         'tables',
                                         'attr_list',
                                         'def_list',
                                         'fenced_code',
                                         'admonition'])


@app.template_filter()
def extract_hostname(url):
    return parse.urlparse(url).netloc


def parse_dt(dt):
    """
    Parse an SQLite datetime, treating it as UTC.
    """
    parsed = datetime.datetime.strptime(dt, '%Y-%m-%d %H:%M:%S')
    return parsed.replace(tzinfo=datetime.timezone.utc)
