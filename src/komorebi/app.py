import datetime
from urllib import parse

from flask import (
    Flask,
    Response,
    abort,
    render_template,
    url_for,
)
import markdown

from komorebi import db, wsgiutils, xmlutils


FEED_ID = "tag:talideon.com,2001:weblog"


app = Flask(__name__)
app.wsgi_app = wsgiutils.ReverseProxied(app.wsgi_app)
app.teardown_appcontext(db.close_connection)


@app.route("/")
def latest():
    sql = """
        SELECT   id, time_c, time_m, link, title, via, note
        FROM     links
        ORDER BY time_c DESC
        LIMIT    40
        """
    return render_template("latest.html", entries=db.query(sql))


@app.route("/archive")
def archive():
    # This is gross.
    sql = """
        SELECT   CAST(SUBSTR(time_c, 0, 5) AS INTEGER) AS "year",
                 CAST(SUBSTR(time_c, 6, 2) AS INTEGER) AS "month",
                 COUNT(*) AS n
        FROM     links
        GROUP BY SUBSTR(time_c, 0, 8)
        ORDER BY SUBSTR(time_c, 0, 5) DESC,
                 SUBSTR(time_c, 6, 2) ASC
        """
    return render_template("archive.html",
                           entries=process_archive(db.query(sql)))


def process_archive(records):
    year = None
    last_month = 0
    for record in records:
        # Pad out to the end of the year.
        if record['year'] != year:
            if last_month != 0:
                for i in range(1, 13 - last_month):
                    yield {
                        'n': 0,
                        'year': year,
                        'month': last_month + i,
                        'part': 'a',
                    }
            year = record['year']
            last_month = 0

        # Pad out between months in a year.
        if record['month'] - 1 != last_month:
            for i in range(1, record['month'] - last_month):
                yield {
                    'n': 0,
                    'year': record['year'],
                    'month': last_month + i,
                    'part': 'b',
                }

        yield record
        last_month = record['month']


@app.route("/feed")
def feed():
    modified = db.query_value("SELECT MAX(time_m) FROM links")
    if modified:
        modified = parse_dt(modified)
        # TODO: ETag

    sql = """
        SELECT   id, time_c, time_m, link, title, via, note
        FROM     links
        ORDER BY time_m DESC
        LIMIT    40
        """

    xml = xmlutils.XMLBuilder()
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

        for entry in db.query(sql):
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
                    xml.content(md(entry['note']), **attrs)

    return Response(xml.as_string(),
                    content_type='application/atom+xml; charset=UTF-8')


@app.route("/<string(length=4):year>-<string(length=2):month>")
def month(year, month):
    dt = datetime.date(int(year), int(month), 1)
    sql = """
        SELECT  id, time_c, time_m, link, title, via, note
        FROM    links
        WHERE   time_c BETWEEN ? AND DATE(?, '+1 month')
        ORDER BY time_c ASC
        """
    entries = list(db.query(sql, (dt.isoformat(), dt.isoformat())))
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
    entry = db.query_row(sql, (entry_id,))
    if entry is None:
        abort(404)
    return render_template("entry.html", entry=entry)


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
