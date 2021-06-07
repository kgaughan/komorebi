"""
Extract build embeds based on target page metadata.
"""

import re
import urllib.error

from . import discovery, html, oembed, ogp


def make_video_facade(src, title, thumb, width, height):
    attrs = {
        "class": "facade",
        "title": title,
        "data-src": src,
        "data-thumb": thumb,
        "data-width": str(width),
        "data-height": str(height),
    }
    # Remove anything that's empty
    for key, value in list(attrs.items()):
        if value is None:
            del attrs[key]
    return html.make("div", attrs=attrs)


def find_iframe(elems) -> html.Element:
    for elem in elems:
        if isinstance(elem, html.Element) and elem.tag == "iframe":
            return elem
    return None


def make_default_facade(doc):
    return doc["html"]


RE_VIMEO_THUMB = re.compile(
    r"^(?P<prefix>(?:.*)/(?:\d+)_)(?P<width>\d+)x(?P<height>\d+)$",
)


def make_vimeo_facade(doc: dict):
    iframe = find_iframe(html.parse(doc["html"]))
    # Fallback to provided HTML if we've no choice
    if iframe is None:
        return doc["html"]
    width = doc["width"]
    height = doc["height"]

    # Adjust the thumbnail size to match the video
    thumb = doc.get("thumbnail_url")
    if thumb:
        match = RE_VIMEO_THUMB.match(thumb)
        if match:
            thumb = f"{match.group('prefix')}{width}x{height}"
    return make_video_facade(
        src=iframe.attrs["src"],
        title=doc.get("title"),
        thumb=thumb,
        width=width,
        height=height,
    )


def make_youtube_facade(doc: dict):
    iframe = find_iframe(html.parse(doc["html"]))
    # Fallback to provided HTML if we've no choice
    if iframe is None:
        return doc["html"]
    width = doc["width"]
    height = doc["height"]
    # Scale up small embeds
    if width < 560:
        height = int(height * 560.0 / width)
        width = 560
    return make_video_facade(
        src=iframe.attrs["src"],
        title=doc.get("title"),
        thumb=doc.get("thumbnail_url"),
        width=width,
        height=height,
    )


FACADE_MAKERS = {
    "Vimeo": make_vimeo_facade,
    "YouTube": make_youtube_facade,
}


def make_markup_from_oembed(doc: dict) -> str:
    title = doc.get("title")

    if doc["type"] == "photo":
        attrs = {
            "href": doc["url"],
            "width": doc["width"],
            "height": doc["height"],
        }
        if title:
            attrs["title"] = title
        return html.make("img", attrs)

    if doc["type"] == "video":
        make_facade = FACADE_MAKERS.get(doc.get("provider_name"), make_default_facade)
        return make_facade(doc)

    # Unsupported oEmbed type
    return None


def make_markup_from_ogp(root: ogp.Root) -> str:
    title = root.get("og:title")
    if title.content is None:
        return None

    video = root.get("og:video")
    if video.content is not None:
        mimetype = video.attrs["type"].content
        # Currently, only iframe embeds are supported
        if mimetype == "text/html":
            return html.make(
                "iframe",
                attrs={
                    "src": video.content,
                    "width": video.attrs["width"].content,
                    "height": video.attrs["height"].content,
                    "frameborder": "0",
                    "sandbox": "allow-same-origin allow-scripts",
                    "allow": "autoplay; clipboard-write; encrypted-media; picture-in-picture",
                    "class": "player",
                },
            )

    return None


def fetch_embed(url):
    try:
        links, meta = discovery.fetch_meta(url)
    except urllib.error.HTTPError:
        return None
    if links:
        doc = oembed.get_oembed(links)
        if doc:
            return make_markup_from_oembed(doc)
    return make_markup_from_ogp(ogp.Root.from_list(meta))
