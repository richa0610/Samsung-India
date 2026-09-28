"""Test-suite safety guard - runs before any test module (and so before anything
imports app.core.config).

The app normally initialises its database when `app.main` is imported
(create_all, column sync, index sync) against whatever `.env` points at - which
on a developer machine is the real, remote database. So the moment the suite
starts, every setting that could reach a database is FORCED (not defaulted) to an
unusable local address, and TESTING=1 switches the import-time work off. Real
values from `.env` are never used: environment variables win over `.env`.

Settings additionally refuses to load if TESTING is set with a non-local database
host (see app/core/config.py), so this fails closed rather than open."""

import os

_UNUSABLE = {
    "TESTING": "1",
    "DB_HOST": "127.0.0.1",
    "DB_PORT": "1",  # nothing listens here: any accidental connection is refused at once
    "DB_USER": "test",
    "DB_PASSWORD": "test",
    "DB_NAME": "test",
    "DB_SSL_CA": "",
    "COMMON_DB_HOST": "127.0.0.1",
    "COMMON_DB_PORT": "1",
    "COMMON_DB_USER": "test",
    "COMMON_DB_PASSWORD": "test",
    "COMMON_DB_NAME": "test",
    "SECRET_KEY": "test-secret-not-used-outside-tests",
    "ALGORITHM": "HS256",
    "ACCESS_TOKEN_EXPIRE_MINUTES": "30",
}
os.environ.update(_UNUSABLE)
