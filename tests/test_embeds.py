import unittest

from komorebi import embeds


class TestEmbeds(unittest.TestCase):
    def test_make_video_facade(self):
        self.assertEqual(
            embeds.make_video_facade(
                src="http://example.com/",
                title=None,
                thumb=None,
                width=None,
                height=None,
            ),
            '<div class="facade" data-src="http://example.com/"></div>',
        )
        self.assertEqual(
            embeds.make_video_facade(
                src="http://example.com/",
                title="Foo",
                thumb="http://example.com/thumb.jpg",
                width=8,
                height=8,
            ),
            '<div class="facade" title="Foo" data-src="http://example.com/" data-thumb="http://example.com/thumb.jpg" data-width="8" data-height="8"></div>',
        )

    def test_make_youtube_facade_missing_html(self):
        with self.assertRaises(KeyError):
            embeds.make_youtube_facade({})

    def test_make_youtube_facade_fallback(self):
        self.assertEqual(
            embeds.make_youtube_facade({"html": "<span>HTML</span>"}),
            "<span>HTML</span>",
        )

    def test_make_youtube_facade_iframe(self):
        self.assertEqual(
            embeds.make_youtube_facade(
                {
                    "html": '<iframe src="https://example.com/video.mpg">',
                    "width": 20,
                    "height": 20,
                }
            ),
            '<div class="facade" data-src="https://example.com/video.mpg" data-width="560" data-height="560"></div>',
        )
        self.assertEqual(
            embeds.make_youtube_facade(
                {
                    "html": '<iframe src="https://example.com/video.mpg">',
                    "width": 20,
                    "height": 10,
                }
            ),
            '<div class="facade" data-src="https://example.com/video.mpg" data-width="560" data-height="280"></div>',
        )
        self.assertEqual(
            embeds.make_youtube_facade(
                {
                    "html": '<iframe src="https://example.com/video.mpg">',
                    "width": 600,
                    "height": 300,
                }
            ),
            '<div class="facade" data-src="https://example.com/video.mpg" data-width="600" data-height="300"></div>',
        )
