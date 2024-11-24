"""
A client for the HeadSpace API.
This client tries to blend in / avoid bot detection by pretending to be a modern browser but
there are a few things that I am not doing below that a browser does do:

- Pre-flight OPTIONS requests. Browser sends these... but the timing of them is a bit odd? At least FireFox
    seems to send the OPTIONS request _after_ the GET/POST. Not sure if this is a bug in the browser/dev tools
    or if this is what's really happening

- Some headers are present on some requests/but not others. At least so far, the "Auth0-Client" header is the
    primary example of this. It's value is a simple json dict that's b64 encoded.

At least so far while building/testing this, I haven't tripped their bot-detection so I'm not going to worry.
"""

import datetime

import aiohttp
import jwt

from .constants import APP_ENV_JS_URL, APP_STATS_URL_BASE, AUTH_URL
from .util.convert import env_js_to_python

try:
    import structlog

    log = structlog.get_logger()

except ImportError:
    import logging

    log = logging.getLogger(__name__)


class HeadSpace:
    """Processes the client request"""

    # No idea what bot mitigations they have in place; we pretend to be a
    #   very modern version of Firefox to avoid any potential issues.
    user_agent = (
        " Mozilla/5.0 (X11; Linux x86_64; rv:131.0) Gecko/20100101 Firefox/131.0"
    )

    def __init__(
        self,
    ) -> None:
        # Common headers that seem to be set for basically every request as far as I can tell.
        # We'll add to this as needed for each request.
        self._headers = {
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Connection": "keep-alive",
            "Sec-Fetch-Dest": "script",
            "Sec-Fetch-Mode": "no-cors",
            "Sec-Fetch-Site": "same-origin",
            "Priority": "u=2",
            "Pragma": "no-cache",
            "Cache-Control": "no-cache",
            # Note: see docs/api/readme.md; it's a very small json dict b64 encoded
            # It is sent on at least SOME requests but doesn't seem to be REQUIRED
            # On one hand, adding it to the requests where it shows up helps us blend in
            #   but on the other hand, it's a bit of a pain to keep it up to date and keep track of
            #   when it's needed.
            # For now, I'm going to leave it out and only add it if I see it's needed.
            # "Auth0-Client": "eyJuYW1lIjoiYXV0aDAuanMiLCJ2ZXJzaW9uIjoiOS4xMy4yIn0=",
            "TE": "trailers",
        }
        # For interacting with Auth0
        self._auth0_client_id: str | None = None
        self._user_name: str | None = None
        self._password: str | None = None

        # For interacting with the Headspace API we need hsId and the auth token
        self._hs_id: str | None = None
        self._auth_token: str | None = None
        self._auth_token_expires: datetime.datetime | None = None

        # Keep track of cookies
        self._session = aiohttp.ClientSession()

    @property
    def user_name(self) -> str | None:
        """Getter for user_name"""
        return self._user_name

    @user_name.setter
    def user_name(self, value: str) -> str | None:
        """Sets user name"""
        if not value:
            raise ValueError("User name cannot be empty")
        self._user_name = value

    @property
    def password(self) -> str | None:
        """Getter for password"""
        return self._password

    @password.setter
    def password(self, value: str) -> str | None:
        """Sets password"""
        if not value:
            raise ValueError("Password cannot be empty")
        self._password = value

    @property
    def auth0_client_id(self) -> str | None:
        """Getter for auth0_client_id"""
        return self._auth0_client_id

    @auth0_client_id.setter
    def auth0_client_id(self, value: str | None) -> None:
        """Sets or clears the auth0_client_id."""
        self._auth0_client_id = value

    @property
    def expiration(self) -> datetime.datetime | None:
        """Getter for auth expiration"""
        return self._auth_token_expires

    @property
    def hs_id(self) -> str | None:
        """Getter for hs_id"""
        return self._hs_id

    async def __aenter__(self):
        """Alternative: See: https://stackoverflow.com/a/67577364"""
        return self

    async def __aexit__(self, *excinfo):
        await self._session.close()

    async def close(self) -> None:
        """Closes the underlying aiohttp session.

        Needed when not using with X as Y context manager pattern."""
        await self._session.close()

    async def _pre_flight_check(self):
        """Common pre-request checks"""
        # TODO: check if auth has expired / refresh it
        # If we have an auth token, add it to the headers
        if self._auth_token is not None:
            self._session.headers["Authorization"] = f"Bearer {self._auth_token}"

        if self._session.closed:
            log.error("session is closed, creating new session")
            self._session = aiohttp.ClientSession()

    async def get_auth0_token(self):
        """Attempts to pull down the env.js file from the Headspace site and extract the
        auth0 client ID from it."""
        # I am 99% sure that this is super long lived and in most cases user can just
        #   set it statically.
        # If already set, don't bother trying to get it again. If user really wants to automate
        #   fetching it again, they can clear what's already set before calling this.
        if self._auth0_client_id is not None:
            raise ValueError("auth0_client_id isn't empty.")

        async with self._session.get(APP_ENV_JS_URL) as resp:
            if resp.status != 200:
                log.error("Something didn't go well!", resp=await resp.text())
                resp.raise_for_status()
            js_text = await resp.text()
            log.debug("got data", js_text=js_text)
            # Now try to transform the JS to python dict
            env = env_js_to_python(js_text)
            log.debug("we have a valid env.js?", env=env)
            # Sanity check
            if "auth0" not in env:
                _e = "parsed env.js does not have auth0 key!"
                log.fatal("%s. got: %s", _e, env)
                raise ValueError(_e)
            if "clientId" not in env["auth0"]:
                _e = "parsed env.js does not have auth0.clientId key!"
                log.fatal("%s. got: %s", _e, env)
                raise ValueError(_e)
            self._auth0_client_id = env["auth0"]["clientId"]
            # We're OK to continue
            log.debug("auth0.clientId discovered!", client_id=self._auth0_client_id)

    async def get_headspace_auth_token(self) -> dict[str, str]:
        """Attempts to get a long-lived auth token for use with Headspace API.
        Essentially redeem the  auth0ID/user/password for a JWT."""
        # pre-flight checks for the request
        if self._auth0_client_id is None:
            raise ValueError("Can't get headspace auth if auth0_client_id is not set!")
        if self.user_name is None:
            raise ValueError("Can't get headspace auth if user_name is not set!")
        if self.password is None:
            raise ValueError("Can't get headspace auth if password is not set!")

        body = {
            "realm": "User-Password-Headspace",
            "audience": "https://api.prod.headspace.com",
            "client_id": self._auth0_client_id,
            "scope": "openid email",
            "grant_type": "http://auth0.com/oauth/grant-type/password-realm",
            "username": self.user_name,
            "password": self.password,
        }

        auth = await self.do_post_request(AUTH_URL, body)
        # Should be a dict with keys:
        #   ['access_token', 'id_token', 'scope', 'expires_in', 'token_type']
        # Both the _token keys are JWTs. We don't have the secret so we can't verify
        #   the signature, but we can still decode the payload.
        # There's some overlap between the two but the I think I only need to decode
        #   part of the id_token. The auth I just pass back to server...
        ##
        # Note debug level logging here because this is sensitive data.
        _d = None
        _a = None

        # Technically, the auth token has the hsId in so we could just decode that
        #   but i'm not sure if that's intentional. It's probably more stable over the long
        #   term to assume that the user ID will be present in the id_token :)
        ##
        if "access_token" not in auth:
            _e = "Auth response missing access_token!"
            log.debug(_e, auth=auth)
            raise ValueError(_e)
        if "id_token" not in auth:
            _e = "Auth response missing id_token!"
            log.debug(_e, auth=auth)
            raise ValueError(_e)

        # We have the two tokens, let's decode/store them as needed
        # TODO: for the decode operations, need to catch possibly invalid tokens?
        _o = {"verify_signature": False}
        _a = jwt.decode(auth["access_token"], options=_o)
        _d = jwt.decode(auth["id_token"], options=_o)

        ##
        # We store the auth token verbatim for use in requests but also need to decode
        #   it to get the expiration time.
        self._auth_token = auth["access_token"]
        log.debug("access_token discovered!", access_token=self._auth_token)

        if "hsId" not in _d:
            _e = "id_token missing hsId!"
            log.debug(_e, decoded=_d)
            raise ValueError(_e)
        self._hs_id = _d["hsId"]
        log.debug("hsId discovered!", hs_id=self._hs_id)

        # Check token issue/expiration times
        if "exp" not in _a:
            _e = "access_token missing exp!"
            log.debug(_e, decoded=_a)
            raise ValueError(_e)

        if "iat" not in _a:
            _e = "access_token missing iat!"
            log.debug(_e, decoded=_a)
            raise ValueError(_e)

        # The raw values will be integers representing seconds since epoch so we don't need
        #   to do any conversion here.
        if _a["exp"] < _a["iat"]:
            _e = "access_token exp is before iat!"
            log.debug(_e, decoded=_a)
            raise ValueError(_e)
        # turn the issued at time into a datetime object
        _now = datetime.datetime.now(datetime.UTC)
        _issued_at = datetime.datetime.fromtimestamp(_a["iat"], datetime.UTC)
        log.info("Authenticated at", at=_issued_at)
        # TODO: account for microsecond differences?
        # at=    datetime.datetime(2024, 11, 24, 21, 45, 48, tzinfo=datetime.timezone.utc)
        # now=datetime.datetime(2024, 11, 24, 21, 45, 47, 972540, tzinfo=datetime.timezone.utc)
        if _issued_at > _now:
            _e = "auth token issued in the future!"
            log.warning(_e, now=_now, at=_issued_at)
            raise ValueError(_e)

        # Ok, timestamps seem legit.
        self._auth_token_expires = datetime.datetime.fromtimestamp(
            _a["exp"], datetime.UTC
        )
        log.info("Authenticated until expiration", at=self._auth_token_expires)
        # TODO: create an async timer to refresh the token before it expires?

    async def do_post_request(self, url: str, data: dict[any, any]) -> dict[str, any]:
        """Does a POST request to the specified URL.

        Args:
            url (str): _description_
            data (dict[any, any]): _description_

        Returns:
            dict[str, any]: _description_
        """
        await self._pre_flight_check()

        log.debug("do_post_request", data=data)
        # TODO: error handling, lots of ways network/json parse can fail...
        async with self._session.post(url, headers=self._headers, json=data) as resp:
            if resp.status != 200:
                log.debug("here is resp", extra={"resp": await resp.text()})
                resp.raise_for_status()
            return await resp.json()

    async def get_user_stats(self) -> dict[str, str]:
        """Attempts to get basic user stats from the Headspace API.
        Stats look like this
            [
                {
                    'currentValue': 1234,
                    'validUntil': None,
                    'id': 12345678, 'label': 'TOTAL_SESSIONS',
                    'userId': 'someUUIDHere', 'previousValue': 1233, 'deletedAt': None, '
                    'clientUpdatedAt': '2000-01-01T01: 02: 03.000Z',
                    'createdAt': '2000-01-01T01: 02: 03.000Z',
                    'updatedAt': '2000-01-01T01: 02: 03.000Z'
                },
             <...>
            ]
        """
        if self._hs_id is None:
            raise ValueError("hs_id is not set!")
        url_params = {
            "userId": self._hs_id,
        }
        user_stats = await self.do_get_request(APP_STATS_URL_BASE, url_params)

        # Each record contains a few fields that we don't care about; drop them
        _delete = [
            # Why even bother?
            "validUntil",
            "deletedAt",
            # Unless they add a new stat, this will be account creation date
            "createdAt",
            # I don't know why this is also reported?
            "clientUpdatedAt",
            # Not sure what this is, but it's not useful to us
            "id",
            # We know this already...
            "userId",
        ]
        for stat in user_stats:
            for _k in _delete:
                stat.pop(_k)
        return user_stats

    async def do_get_request(
        self, url: str, data: dict | None = None
    ) -> dict[str, any]:
        """does a get request to the specified URL

        Args:
            url (str): _description_
            data (dict | None, optional): _description_. Defaults to None.

        Returns:
            dict[str, any]: _description_
        """
        await self._pre_flight_check()

        # TODO: error handling, lots of ways network/json parse can fail...
        async with self._session.get(url, headers=self._headers, params=data) as resp:
            if resp.status != 200:
                log.debug("here is resp", extra={"resp": await resp.text()})
                resp.raise_for_status()
            return await resp.json()


## TODO: errors to handle
# aiohttp.client_exceptions.ClientResponseError: 403
# {"error":"invalid_grant","error_description":"We couldn\'t find your account. Please try again or sign up for a new account."}
# aiohttp.client_exceptions.ClientResponseError: 404
# {'resp': '{"errors":[{"status":404,"title":"Not Found","detail":"Not Found","data":null}]}'}
