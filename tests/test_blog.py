from komorebi import blog, db


def test_process_archive_no_entries():
    assert list(blog.process_archive([])) == []


def test_process_archive_single():
    single = [db.ArchiveMonth(year=2020, month=1, n=42)]
    assert list(blog.process_archive(single)) == single


def test_process_archive_span():
    span = [db.ArchiveMonth(year=2020, month=n + 1, n=42 + n) for n in range(3)]
    assert list(blog.process_archive(span)) == span


def test_process_archive_month_gap():
    assert list(
        blog.process_archive(
            [
                {"year": 2020, "month": 1, "n": 42},
                {"year": 2020, "month": 3, "n": 44},
            ]
        )
    ) == [
        {"year": 2020, "month": 1, "n": 42},
        {"year": 2020, "month": 2, "n": 0},
        {"year": 2020, "month": 3, "n": 44},
    ]


def test_process_archive_year_gap():
    assert list(
        blog.process_archive(
            [
                # Should fill in the start of the year
                {"year": 2020, "month": 11, "n": 1},
                # Should fill in this gap
                {"year": 2021, "month": 2, "n": 1},
            ]
        )
    ) == [
        *[{"year": 2020, "month": 1 + n, "n": 0} for n in range(10)],
        {"year": 2020, "month": 11, "n": 1},
        {"year": 2020, "month": 12, "n": 0},
        {"year": 2021, "month": 1, "n": 0},
        {"year": 2021, "month": 2, "n": 1},
    ]
