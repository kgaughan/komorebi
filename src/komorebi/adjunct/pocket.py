import datetime
import json
import typing as t
from urllib import parse, request


class Actions:
    """
    Batches together a set of actions to take.
    """

    def __init__(self):
        super().__init__()
        self.actions = []

    def _append(self, **params):
        for key, value in list(params.items()):
            if not value:
                del params[key]
            elif isinstance(value, datetime.datetime):
                # Treat naive timezones as UTC for sanity's sake.
                if value.tzinfo is None:
                    value = value.replace(tzinfo=datetime.timezone.utc)
                params[key] = int(value.timestamp())
            elif key == "tags":
                params[key] = ",".join(value)
        self.actions.append(params)

    def add(
        self,
        url: str,
        title: t.Optional[str] = None,
        tags: t.Sequence[str] = (),
        ref_id: t.Optional[str] = None,
    ):
        self._append(action="add", url=url, title=title, tags=tags, ref_id=ref_id)

    def archive(self, item_id: str):
        self._append(action="archive", item_id=item_id)

    def delete(self, item_id: str):
        self._append(action="delete", item_id=item_id)

    def favorite(self, item_id: str):
        self._append(action="favorite", item_id=item_id)

    def unfavorite(self, item_id: str):
        self._append(action="unfavorite", item_id=item_id)

    def tags_add(self, item_id: str, tags: t.Sequence[str]):
        self._append(action="tags_add", item_id=item_id, tags=tags)

    def tags_remove(self, item_id: str, tags: t.Sequence[str]):
        self._append(action="tags_remove", item_id=item_id, tags=tags)

    def tags_replace(self, item_id: str, tags: t.Sequence[str]):
        self._append(action="tags_replace", item_id=item_id, tags=tags)

    def tags_clear(self, item_id: str):
        self._append(action="tags_clear", item_id=item_id)

    def tag_rename(self, old_tag: str, new_tag: str):
        self._append(action="tag_rename", old_tag=old_tag, new_tag=new_tag)


class Client:
    """
    Pocket client.
    """

    PREFIX = "https://getpocket.com/v3/"

    def __init__(self, consumer_key: str, access_token: t.Optional[str] = None):
        super().__init__()
        self._consumer_key = consumer_key
        self.access_token = access_token

    def make_request(self, method: str, params: t.Optional[dict] = None):
        data = {"consumer_key": self._consumer_key}
        if self.access_token is not None:
            data["access_token"] = self.access_token
        if params is not None:
            data.update(params)

        req = request.Request(
            parse.urljoin(self.PREFIX, method),
            data=json.dumps(data).encode("utf-8"),
            headers={
                "Content-Type": "application/json; charset=UTF8",
                "X-Accept": "application/json",
                "User-Agent": "komorebi-pocket-client/1.0",
            },
            method="POST",
        )
        with request.urlopen(req) as response:
            return json.load(response)

    def oauth_request(self, redirect_uri: str, state: t.Optional[str] = None):
        params = {"redirect_uri": redirect_uri}
        if state is not None:
            params["state"] = state
        return self.make_request("oauth/request", params)

    def oauth_authorize(self, code: str):
        return self.make_request("oauth/authorize", {"code": code})

    def add(
        self,
        url: str,
        title: t.Optional[str] = None,
        tags: t.Sequence[str] = (),
        tweet_id: t.Optional[str] = None,
    ):
        params = {
            "url": url,
            "tags": ",".join(tags),
        }
        for key, value in [("title", title), ("tweet_id", tweet_id)]:
            if value is not None:
                params[key] = value
        return self.make_request("add", params)

    def modify(self, actions: Actions):
        return self.make_request("send", {"actions": actions.actions})

    def retrieve(self, params: dict):
        return self.make_request("get", params)
