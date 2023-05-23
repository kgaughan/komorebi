"""
Extract build embeds based on target page metadata.
"""

import re
import typing as t
import urllib.error

from . import discovery, html, oembed, ogp


def make_video_facade(
    src: t.Optional[str],
    title: t.Optional[str],
    thumb: t.Optional[str],
    width: t.Optional[int],
    height: t.Optional[int],
) -> str:
    attrs = {
        "class": "facade",
        "title": title,
        "data-src": src,
        "data-thumb": thumb,
        "data-width": width,
        "data-height": height,
    }
    # Remove anything that's empty; cast the rest
    for key, value in list(attrs.items()):
        if value is None:
            del attrs[key]
        else:
            attrs[key] = str(value)
    return html.make("div", attrs=attrs)


def find_iframe(elems: html.Element) -> t.Optional[html.Element]:
    return next(
        (
            elem
            for elem in elems
            if isinstance(elem, html.Element) and elem.tag == "iframe"
        ),
        None,
    )


def make_default_facade(doc: dict) -> str:
    return doc["html"]


RE_VIMEO_THUMB = re.compile(
    r"^(?P<prefix>(?:.*)/(?:\d+)_)(?P<width>\d+)x(?P<height>\d+)$",
)


def make_vimeo_facade(doc: dict) -> str:
    iframe = find_iframe(html.parse(doc["html"]))
    # Fallback to provided HTML if we've no choice
    if iframe is None:
        return doc["html"]
    width = doc["width"]
    height = doc["height"]

    # Adjust the thumbnail size to match the video
    thumb = doc.get("thumbnail_url")
    if thumb:
        if match := RE_VIMEO_THUMB.match(thumb):
            thumb = f"{match.group('prefix')}{width}x{height}"
    return make_video_facade(
        src=iframe.attrs["src"],
        title=doc.get("title"),
        thumb=thumb,
        width=width,
        height=height,
    )


def make_youtube_facade(doc: dict) -> str:
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


def make_markup_from_oembed(doc: dict) -> t.Optional[str]:
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
        provider = doc.get("provider_name")
        if provider is not None:
            return FACADE_MAKERS.get(provider, make_default_facade)(doc)

    # Unsupported oEmbed type
    return None


def make_markup_from_ogp(props: t.Sequence[ogp.Property]) -> t.Optional[str]:
    return next(
        (
            html.make(
                "iframe",
                attrs={
                    "src": video.value,
                    "width": video.metadata["width"],
                    "height": video.metadata["height"],
                    "frameborder": "0",
                    "sandbox": "allow-same-origin allow-scripts",
                    "allow": "autoplay; clipboard-write; encrypted-media; picture-in-picture",
                    "class": "player",
                },
            )
            for video in ogp.find(props, "video")
            if video.metadata["type"] == "text/html"
        ),
        None,
    )


def fetch_embed(url: str) -> t.Optional[str]:
    try:
        links, meta = discovery.fetch_meta(url)
    except urllib.error.HTTPError:
        return None
    if links:
        if doc := oembed.get_oembed(links):
            return make_markup_from_oembed(doc)
    return make_markup_from_ogp(ogp.parse(meta))
