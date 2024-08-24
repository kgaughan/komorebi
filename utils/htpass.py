#!/usr/bin/env python3

import argparse
import getpass
import os.path
import sys

from passlib import apache, pwd


def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="htpasswd editor")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--list", action="store_true", help="List users")
    group.add_argument("--add", action="store_true", help="Add user")
    group.add_argument("--remove", action="store_true", help="Remove user")
    parser.add_argument("--user", help="Username", default=getpass.getuser())
    parser.add_argument("--gen", action="store_true", help="Generate a password")
    parser.add_argument("--path", required=True, help="Path of htaccess file")
    return parser


def main():
    args = make_parser().parse_args()

    new = args.add and not os.path.exists(args.path)
    ht = apache.HtpasswdFile(args.path, new=new, autosave=True)

    if args.list:
        for user in ht.users():
            print(user)  # noqa: T201
    elif args.remove:
        ht.delete(args.user)
    elif args.add:
        if args.gen:
            passwd = pwd.genword(entropy="secure", charset="ascii_72", length=16)
            print("Password:", passwd)  # noqa: T201
        else:
            passwd = getpass.getpass()
        ht.set_password(args.user, passwd)


if __name__ == "__main__":
    sys.exit(main())
