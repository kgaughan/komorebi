import os
import sqlite3

from flask import g


def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db_path = os.environ.get('LINKLOG_DB_PATH', 'db.sqlite')
        db = g._database = sqlite3.connect(db_path)
        db.row_factory = sqlite3.Row
    return db


def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


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
