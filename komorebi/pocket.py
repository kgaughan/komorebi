import json
from urllib import parse, request


class Client:
    """
    Pocket client.
    """

    PREFIX = "https://getpocket.com/v3/"

    def __init__(self, consumer_key, access_token=None):
        super().__init__()
        self._consumer_key = consumer_key
        self.access_token = access_token

    def make_request(self, method, params=None):
        data = {"consumer_key": self._consumer_key}
        if self.access_token is not None:
            data["access_token"] = self.access_token
        if params is not None:
            data.update(params)

        req = request.Request(
            parse.urljoin(self.PREFIX, method),
            data=json.dumps(data),
            headers={
                "Content-Type": "application/json; charset=UTF8",
                "X-Accept": "application/json",
                "User-Agent": "komorebi-pocket-client/1.0",
            },
            method="POST",
        )
        with request.urlopen(req) as response:
            return json.load(response)

    def oauth_request(self, redirect_uri, state=None):
        params = {"redirect_uri": redirect_uri}
        if state is not None:
            params["state"] = state
        return self.make_request("oauth/request", params)

    def oauth_authorize(self, code):
        return self.make_request("oauth/authorize", {"code": code})

    def add(self, url, title=None, tags=(), tweet_id=None):
        params = {
            "url": url,
            "tags": ",".join(tags),
        }
        for key, value in [("title", title), ("tweet_id", tweet_id)]:
            if value is not None:
                params[key] = value
        return self.make_request("add", params)

    def modify(self, actions):
        return self.make_request("send", {"actions": actions.actions})

    def retrieve(self, params):
        return self.make_request("get", params)


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
            elif key == "tags":
                params[key] = ",".join(value)
        self.actions.append(params)

    def add(self, url, title=None, tags=(), tweet_id=None):
        self._append(action="add", url=url, title=title, tags=tags, ref_id=tweet_id)

    def archive(self, item_id):
        self._append(action="archive", item_id=item_id)

    def delete(self, item_id):
        self._append(action="delete", item_id=item_id)

    def favorite(self, item_id):
        self._append(action="favorite", item_id=item_id)

    def unfavorite(self, item_id):
        self._append(action="unfavorite", item_id=item_id)

    def tags_add(self, item_id, tags):
        self._append(action="tags_add", item_id=item_id, tags=tags)

    def tags_remove(self, item_id, tags):
        self._append(action="tags_remove", item_id=item_id, tags=tags)

    def tags_replace(self, item_id, tags):
        self._append(action="tags_replace", item_id=item_id, tags=tags)

    def tags_clear(self, item_id):
        self._append(action="tags_clear", item_id=item_id)

    def tag_rename(self, old_tag, new_tag):
        self._append(action="tag_rename", old_tag=old_tag, new_tag=new_tag)
