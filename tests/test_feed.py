import datetime
from pathlib import Path

import pytest

from komorebi import db, feed
from komorebi.app import create_app


@pytest.fixture()
def application():
    result = create_app(testing=True)
    # other setup can go here
    yield result
    # add any cleanup here


def test_minimal_feed(application):
    with open(Path(__file__).parent / "golden" / "minimal.atom") as fh:
        expected = fh.read().strip()
    with application.app_context():
        contents = feed.generate_feed(
            title="Title",
            author="Author",
            feed_id="urn:uuid:00000000-0000-0000-0000-000000000000",
            entries=[],
        )
    assert contents == expected


def test_empty_feed(application):
    with open(Path(__file__).parent / "golden" / "empty.atom") as fh:
        expected = fh.read().strip()
    with application.app_context():
        contents = feed.generate_feed(
            title="Title",
            author="Author",
            feed_id="urn:uuid:00000000-0000-0000-0000-000000000000",
            entries=[],
            subtitle="Subtitle",
            rights="Rights",
            modified=datetime.datetime(
                year=1970,
                month=2,
                day=1,
                hour=12,
                minute=0,
                second=59,
                tzinfo=datetime.UTC,
            ),
        )
    assert contents == expected


def test_with_entry(application):
    with open(Path(__file__).parent / "golden" / "minimal-entry.atom") as fh:
        expected = fh.read().strip()
    with application.app_context():
        contents = feed.generate_feed(
            title="Title",
            author="Author",
            feed_id="tag:example.com,2005:komorebi",
            entries=[
                db.Entry(
                    id=123,
                    title="This is the title",
                    time_c=datetime.datetime.fromisoformat("2023-12-11 10:09:08"),
                    time_m=datetime.datetime.fromisoformat("2024-12-11 10:09:08"),
                    link=None,
                    via=None,
                    note=None,
                    html=None,
                ),
            ],
        )
    assert contents == expected


def test_with_full_entry(application):
    with open(Path(__file__).parent / "golden" / "full-entry.atom") as fh:
        expected = fh.read().strip()
    with application.app_context():
        contents = feed.generate_feed(
            title="Title",
            author="Author",
            feed_id="tag:example.com,2005:komorebi",
            entries=[
                db.Entry(
                    id=123,
                    title="This is the title",
                    time_c=datetime.datetime.fromisoformat("2023-12-11 10:09:08"),
                    time_m=datetime.datetime.fromisoformat("2024-12-11 10:09:08"),
                    link="http://example.com/thingy/",
                    via="http://example.com/via/",
                    note="This is a note",
                    html="This is some HTML",
                ),
            ],
        )
    assert contents == expected
