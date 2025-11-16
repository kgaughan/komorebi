"""
A partial replacement for passlib, implementing an equivalent of its
HtpasswdFile class and supporting functionality.

It comes with a simple tool for manipulating JSONPasswd files.
"""

import argparse
import base64
import getpass
import hashlib
import json
import secrets
import typing as t


class UnknownAlgorithmError(Exception):
    """Raised when an entry has either an unknown algorithm or none."""


class ScryptParams(t.TypedDict):
    n: int
    r: int
    p: int


class ScryptEntry(t.TypedDict):
    alg: t.Literal["scrypt"]
    key: str
    salt: str
    params: ScryptParams


def scrypt_construct(passwd: bytes, *, salt_len: int = 32, n: int = 1 << 14, r: int = 8, p: int = 1) -> ScryptEntry:
    """Construct an entry from a password using scrypt."""
    salt = secrets.token_bytes(salt_len)
    key = hashlib.scrypt(passwd, salt=salt, n=n, r=r, p=p)
    return ScryptEntry(
        alg="scrypt",
        key=base64.b64encode(key).decode("ascii"),
        salt=base64.b64encode(salt).decode("ascii"),
        params=ScryptParams(n=n, r=r, p=p),
    )


def scrypt_check(passwd: bytes, entry: ScryptEntry) -> bool:
    """Check if a password matches the given entry using scrypt."""
    key = hashlib.scrypt(
        passwd,
        salt=base64.b64decode(entry["salt"].encode("ascii")),
        n=entry["params"]["n"],
        r=entry["params"]["r"],
        p=entry["params"]["p"],
    )
    return secrets.compare_digest(key, base64.b64decode(entry["key"].encode("ascii")))


class JSONPasswdFile:
    """A class to manage user credentials stored in a JSON file.

    ## File Format

    The JSON file should contain a dictionary where keys are usernames and
    values are structured data for checking password validity.

    The outer structure is as follows:

    ```json
    {
      "metadata": {
        "type": "tag:talideon.com,2025:jsonpasswd",
        "version": 1
      },
      "users": {
        "<username1>": { ... },
        "<username2>": { ... }
      }
    }

    For the benefit of tools like file(1), the file should start with the
    metadata entry.

    Each value entry has the format:

    ```json
    {
      "alg": "scrypt",
      "key": "<hashed_password>",
      "salt": "<salt_value>",
      "params": {
        "n": <N_value>,
        "r": <r_value>,
        "p": <p_value>
      }
    }
    ```

    Note that the salt and hashed password key are base64-encoded.

    Currently only the "scrypt" algorithm is supported.
    """

    # This is just an initial stab and I don't expect it to the the final
    # product.
    _implementations: t.ClassVar = {
        "scrypt": {
            "entry": ScryptEntry,
            "construct": scrypt_construct,
            "check": scrypt_check,
        }
    }

    def __init__(self, filepath: str, implementation: str = "scrypt"):
        self.filepath = filepath
        self.implementation = implementation
        self.users = self._load()

    def _load(self) -> dict:
        try:
            with open(self.filepath) as fh:
                payload = json.load(fh)
        except FileNotFoundError:
            return {}

        # We won't bother checking the metadata for now, just check the entries
        # to make sure they're well-formed enough.
        result = {}
        for user, entry in payload.get("users", {}).items():
            impl = self._implementations.get(entry.get("alg"))
            if impl is not None:
                result[user] = entry
        return result

    def _save(self):
        with open(self.filepath, "w") as fh:
            payload = {
                "metadata": {"type": "tag:talideon.com,2025:jsonpasswd", "version": 1},
                "users": self.users,
            }
            json.dump(payload, fh)

    def set_password(self, username: str, password: str):
        self.users[username] = self._implementations[self.implementation]["construct"](password.encode("utf-8"))
        self._save()

    def check_password(self, username: str, password: str) -> bool:
        entry = self.users.get(username)
        if entry is None:
            return False
        if entry.get("alg") is None:
            raise UnknownAlgorithmError(f"No algorithm specified for {username}")
        impl = self._implementations.get(entry.get("alg"))
        if impl is None:
            raise UnknownAlgorithmError(f"Unknown algorithm '{entry['alg']}' specified for {username}")

        return impl["check"](password.encode("utf-8"), entry)

    def delete(self, username) -> bool:
        if username in self.users:
            del self.users[username]
            self._save()
            return True
        return False


def make_parser() -> argparse.ArgumentParser:  # pragma; no cover
    parser = argparse.ArgumentParser(description="jsonpasswd editor")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--list", action="store_true", help="List users")
    group.add_argument("--add", action="store_true", help="Add user")
    group.add_argument("--remove", action="store_true", help="Remove user")
    group.add_argument("--check", action="store_true", help="Check a user's password")
    parser.add_argument("--user", help="Username", default=getpass.getuser())
    parser.add_argument("--gen", action="store_true", help="Generate a password")
    parser.add_argument("--length", type=int, help="Length of password to generate", default=16)
    parser.add_argument("--path", required=True, help="Path of passwd.json file")
    return parser


"""passlib's ascii_72 charset"""
ASCII_72 = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!@#$%^&*?/"


def main() -> None:  # pragma: no cover
    args = make_parser().parse_args()

    ht = JSONPasswdFile(args.path)

    if args.list:
        for user in ht.users:
            print(user)  # noqa: T201
    elif args.remove:
        ht.delete(args.user)
    elif args.add:
        if args.gen:
            passwd = "".join(secrets.choice(ASCII_72) for _ in range(args.length))
            print("User:", args.user)  # noqa: T201
            print("Password:", passwd)  # noqa: T201
        else:
            passwd = getpass.getpass()
        ht.set_password(args.user, passwd)
    elif args.check:
        passwd = getpass.getpass()
        if ht.check_password(args.user, passwd):
            print("Password is valid")  # noqa: T201
        else:
            print("Password is invalid")  # noqa: T201


if __name__ == "__main__":
    main()
