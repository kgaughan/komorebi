import datetime
import sqlite3
import typing as t

from flask import current_app, g

from .adjunct import time


def get_db() -> sqlite3.Connection:
    con = getattr(g, "_database", None)
    if con is None:
        db_path = current_app.config.get("DB_PATH", "db.sqlite")
        con = g._database = sqlite3.connect(db_path)  # pylint: disable=E0237
        con.row_factory = sqlite3.Row
    return con


def close_connection(req):
    con = getattr(g, "_database", None)
    if con is not None:
        cur = con.cursor()
        try:
            cur.execute("PRAGMA optimize")
        finally:
            cur.close()
        con.close()
    return req


def execute(sql: str, args: tuple = ()) -> int | None:
    con = get_db()
    cur = con.cursor()
    cur.arraysize = 50
    try:
        cur.execute(sql, args)
        result = cur.lastrowid
        con.commit()
        return result
    finally:
        cur.close()


def query(sql: str, args: tuple = ()) -> t.Iterator:
    con = get_db()
    cur = con.cursor()
    try:
        cur.execute(sql, args)
        yield from iter(cur.fetchone, None)
    finally:
        cur.close()


def query_row(sql: str, args: tuple = (), *, default=None):
    con = get_db()
    cur = con.cursor()
    try:
        cur.execute(sql, args)
        for row in iter(cur.fetchone, None):
            return row
    finally:
        cur.close()
    return default


def query_value(sql: str, args: tuple = (), *, default: int | str | None = None) -> int | str | None:
    con = get_db()
    cur = con.cursor()
    try:
        cur.execute(sql, args)
        for row in iter(cur.fetchone, None):
            return row[0]
    finally:
        cur.close()
    return default


def query_latest() -> t.Iterator:
    return query(
        """
        SELECT    links.id, time_c, time_m, link, title, via, note,
                  html
        FROM      links
        LEFT JOIN oembed ON links.id = oembed.id
        ORDER BY  time_c DESC
        LIMIT     40
        """
    )


def query_archive() -> t.Iterator:
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


def query_month(year: int, month: int) -> list:
    sql = """
        SELECT    links.id, time_c, time_m, link, title, via, note, html
        FROM      links
        LEFT JOIN oembed ON links.id = oembed.id
        WHERE     time_c BETWEEN ? AND DATE(?, '+1 month')
        ORDER BY  time_c ASC
        """
    dt = datetime.date(year, month, 1)
    return list(query(sql, (dt.isoformat(), dt.isoformat())))


def query_entry(entry_id: int):
    return query_row(
        """
        SELECT    links.id, time_c, time_m, link, title, via, note, html
        FROM      links
        LEFT JOIN oembed ON links.id = oembed.id
        WHERE     links.id = ?
        """,
        (entry_id,),
    )


def add_entry(link: str, title: str, via: str, note: str):
    if link.strip() == "":
        link = None  # type: ignore
    if via.strip() == "":
        via = None  # type: ignore
    if note.strip() == "":
        note = None  # type: ignore

    return execute(
        """
        INSERT
        INTO    links (link, title, via, note)
        VALUES  (?, ?, ?, ?)
        """,
        (link, title, via, note),
    )


def update_entry(entry_id: int, link: str, title: str, via: str, note: str) -> int | None:
    if link.strip() == "":
        link = None  # type: ignore
    if via.strip() == "":
        via = None  # type: ignore
    if note.strip() == "":
        note = None  # type: ignore

    return execute(
        """
        UPDATE  links
        SET     link = ?, title = ?, via = ?, note = ?,
                time_m = DATETIME('now')
        WHERE   id = ?
        """,
        (link, title, via, note, entry_id),
    )


def query_last_modified() -> datetime.datetime | None:
    modified = query_value("SELECT MAX(time_m) FROM links")
    if modified:
        return time.parse_dt(modified)  # type: ignore
    return None


def add_oembed(entry_id: int, html: str) -> None:
    execute(
        """
        INSERT
        INTO    oembed (id, html)
        VALUES  (?, ?)
        """,
        (entry_id, html),
    )
