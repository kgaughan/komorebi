import datetime
import typing as t

import firebirdsql
from flask import Flask, current_app, g

Scalar = int | float | str | bytes | datetime.datetime | None


def get_connection() -> firebirdsql.Connection:
    if "db" not in g:
        g.db = firebirdsql.connect(
            host=current_app.config.get("DB_HOST", "localhost"),
            database=current_app.config["DB_DATABASE"],
            port=3050,
            user=current_app.config["DB_USER"],
            password=current_app.config["DB_PASSWORD"],
        )
    return g.db


def close_db(_):
    conn = g.pop("db", None)
    if conn is not None:
        conn.commit()
        conn.close()


def init_app(app: Flask) -> None:
    app.teardown_appcontext(close_db)


def execute(sql: str, args: tuple[Scalar, ...] = ()) -> int | None:
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(sql, args)
        if returned := cur.fetchone():
            return returned[0]
    finally:
        cur.close()
    return None


def query(sql: str, args: tuple[Scalar, ...] = ()) -> t.Iterator:
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(sql, args)
        yield from cur.itermap()
    finally:
        cur.close()


def query_row(sql: str, args: tuple[Scalar, ...] = (), *, default=None) -> dict[str, Scalar] | None:
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(sql, args)
        if row := cur.fetchonemap():
            return row
    finally:
        cur.close()
    return default


def query_value(sql: str, args: tuple[Scalar, ...] = (), *, default: Scalar = None) -> Scalar:
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(sql, args)
        if row := cur.fetchone():
            return row[0]
    finally:
        cur.close()
    return default


class Entry(t.TypedDict):
    id: int
    title: str
    time_c: datetime.datetime
    time_m: datetime.datetime
    link: str | None
    via: str | None
    note: str | None
    html: str | None


def query_latest() -> t.Iterator[Entry]:
    return query(
        """
        SELECT    links.id, time_c, time_m, link, title, via, note, html
        FROM      links
        LEFT JOIN oembed ON links.id = oembed.id
        ORDER BY  time_c DESC
        ROWS      40
        """
    )


class ArchiveMonth(t.TypedDict):
    year: int
    month: int
    n: int


def query_archive() -> t.Iterator[ArchiveMonth]:
    return query(
        """
        SELECT   EXTRACT(YEAR FROM time_c) AS "year",
                 EXTRACT(MONTH FROM time_c) AS "month",
                 COUNT(*) AS n
        FROM     links
        GROUP BY EXTRACT(YEAR FROM time_c), EXTRACT(MONTH FROM time_c)
        ORDER BY EXTRACT(YEAR FROM time_c) DESC, EXTRACT(MONTH FROM time_c) ASC
        """
    )


def query_month(year: int, month: int) -> t.Iterator[Entry]:
    dt = datetime.date(year, month, 1).isoformat()
    return query(
        """
        SELECT    links.id, time_c, time_m, link, title, via, note, html
        FROM      links
        LEFT JOIN oembed ON links.id = oembed.id
        WHERE     time_c BETWEEN ? AND DATEADD(1 MONTH TO ?)
        ORDER BY  time_c ASC
        """,
        (dt, dt),
    )


def query_entry(entry_id: int) -> Entry | None:
    return query_row(
        """
        SELECT    links.id, time_c, time_m, link, title, via, note, html
        FROM      links
        LEFT JOIN oembed ON links.id = oembed.id
        WHERE     links.id = ?
        """,
        (entry_id,),
    )  # type: ignore


def add_entry(
    link: str | None,
    title: str,
    via: str | None,
    note: str | None,
) -> int:
    if link is not None and link.strip() == "":
        link = None
    if via is not None and via.strip() == "":
        via = None
    if note is not None and note.strip() == "":
        note = None

    return (
        execute(
            """
            INSERT
            INTO    links (link, title, via, note)
            VALUES  (?, ?, ?, ?)
            RETURNING id
            """,
            (link, title, via, note),
        )
        or 0
    )


def update_entry(
    entry_id: int,
    link: str | None,
    title: str,
    via: str | None,
    note: str | None,
) -> int | None:
    if link is not None and link.strip() == "":
        link = None
    if via is not None and via.strip() == "":
        via = None
    if note is not None and note.strip() == "":
        note = None

    return execute(
        """
        UPDATE  links
        SET     link = ?, title = ?, via = ?, note = ?,
                time_m = CURRENT_TIMESTAMP
        WHERE   id = ?
        """,
        (link, title, via, note, entry_id),
    )


def query_last_modified() -> datetime.datetime | None:
    return query_value("SELECT MAX(time_m) FROM links")  # type: ignore


def add_oembed(entry_id: int, html: str) -> int | None:
    return execute(
        """
        INSERT
        INTO    oembed (id, html)
        VALUES  (?, ?)
        """,
        (entry_id, html),
    )
