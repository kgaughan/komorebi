import datetime
import os
import sqlite3
from sqlite3 import IntegrityError

from flask import current_app, g

from . import time


def get_db():
    db = getattr(g, "_database", None)
    if db is None:
        db_path = current_app.config.get("DB_PATH", "db.sqlite")
        db = g._database = sqlite3.connect(db_path)
        db.row_factory = sqlite3.Row
    return db


def close_connection(exception):
    db = getattr(g, "_database", None)
    if db is not None:
        db.close()


def execute(sql, args=()):
    con = get_db()
    cur = con.cursor()
    try:
        cur.execute(sql, args)
        result = cur.lastrowid
        con.commit()
        return result
    finally:
        cur.close()


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


def query_latest():
    return query(
        """
        SELECT    links.id, time_c, time_m, link, title, via, note,
                  html, width, height
        FROM      links
        LEFT JOIN oembed ON links.id = oembed.id
        ORDER BY  time_c DESC
        LIMIT     40
        """
    )


def query_archive():
    # This is gross.
    return query(
        """
        SELECT   CAST(SUBSTR(time_c, 0, 5) AS INTEGER) AS "year",
                 CAST(SUBSTR(time_c, 6, 2) AS INTEGER) AS "month",
                 COUNT(*) AS n
        FROM     links
        GROUP BY SUBSTR(time_c, 0, 8)
        ORDER BY SUBSTR(time_c, 0, 5) DESC,
                 SUBSTR(time_c, 6, 2) ASC
        """
    )


def query_month(year, month):
    sql = """
        SELECT    links.id, time_c, time_m, link, title, via, note,
                  html, width, height
        FROM      links
        LEFT JOIN oembed ON links.id = oembed.id
        WHERE     time_c BETWEEN ? AND DATE(?, '+1 month')
        ORDER BY  time_c ASC
        """
    dt = datetime.date(year, month, 1)
    return list(query(sql, (dt.isoformat(), dt.isoformat())))


def query_entry(entry_id):
    return query_row(
        """
        SELECT    links.id, time_c, time_m, link, title, via, note,
                  html, width, height
        FROM      links
        LEFT JOIN oembed ON links.id = oembed.id
        WHERE     links.id = ?
        """,
        (entry_id,),
    )


def add_entry(link, title, via, note):
    if link.strip() == "":
        link = None
    if via.strip() == "":
        via = None
    if note.strip() == "":
        note = None

    return execute(
        """
        INSERT
        INTO    links (link, title, via, note)
        VALUES  (?, ?, ?, ?)
        """,
        (link, title, via, note),
    )


def update_entry(entry_id, link, title, via, note):
    if link.strip() == "":
        link = None
    if via.strip() == "":
        via = None
    if note.strip() == "":
        note = None

    return execute(
        """
        UPDATE  links
        SET     link = ?, title = ?, via = ?, note = ?,
                time_m = DATETIME('now')
        WHERE   id = ?
        """,
        (link, title, via, note, entry_id),
    )


def query_last_modified():
    modified = query_value("SELECT MAX(time_m) FROM links")
    if modified:
        modified = time.parse_dt(modified, tz=None)
    return modified


def add_oembed(entry_id, html, width, height):
    execute(
        """
        INSERT
        INTO    oembed (id, html, width, height)
        VALUES  (?, ?, ?, ?)
        """,
        (entry_id, html, width, height),
    )
