"""For testing the API client, we have quite a few fixtures to set up to mock async loop and http responses."""

import datetime

import jwt
import pytest
from aioresponses import aioresponses

JWT_SECRET = "secretSquirrel"


@pytest.fixture
def mock_username():
    yield "test_user_name"


@pytest.fixture
def mock_headspace_user_id():
    # True form is HSUSER_some_long_string_here
    yield "mock_headspace_user_id"


@pytest.fixture
def mock_password():
    yield "test_password"


@pytest.fixture
def mock_aioresponse():
    with aioresponses() as m:
        yield m


@pytest.fixture
def mock_auth0_client_id():
    yield "test_client_id"


@pytest.fixture
def mock_issued_at():
    yield datetime.datetime.now(datetime.UTC)


@pytest.fixture
def mock_expires_at(mock_issued_at):
    yield mock_issued_at + datetime.timedelta(seconds=3600)


@pytest.fixture
def mock_valid_access_token(
    mock_headspace_user_id, mock_username, mock_issued_at, mock_expires_at
):
    """
    Generate a JWT that looks like what we'd expect from the auth0 service
    """
    _t = {
        "https://api.prod.headspace.com/hsId": mock_headspace_user_id,
        "https://api.prod.headspace.com/connection": "User-Password-Headspace",
        "https://api.prod.headspace.com/providerId": mock_username,
        "https://api.prod.headspace.com/hsPlatform": "DESKTOP",
        "iss": "https://auth.headspace.com/",
        "sub": "auth0|some_test_sub",
        "aud": [
            "https://api.prod.headspace.com",
            "https://b2c-prod-headspace.auth0.com/userinfo",
        ],
        # issued at
        "iat": mock_issued_at.timestamp(),
        # Expires at
        "exp": mock_expires_at.timestamp(),
        "scope": "openid email",
        "gty": "password",
        # azp is authorized party
        "azp": "some_test_azp",
    }
    yield jwt.encode(_t, JWT_SECRET, algorithm="HS256")


@pytest.fixture
def mock_invalid_access_token(mock_issued_at, mock_expires_at):
    """
    The access token is - largely - just passed through to the API.
    Just for sanity, client does check the issued/expiration times.

    We explicitly omit the 'exp' field here to create an invalid token.
    """
    _t = {
        # issued at
        "iat": mock_issued_at.timestamp(),
        # azp is authorized party
        "azp": "some_test_azp",
    }
    yield jwt.encode(_t, JWT_SECRET, algorithm="HS256")


@pytest.fixture
def mock_valid_id_token(
    mock_headspace_user_id, mock_username, mock_issued_at, mock_expires_at
):
    """Same as above, but for the ID token. There is some overlap between them."""

    _t = {
        "hsId": mock_headspace_user_id,
        "email": mock_username,
        "email_verified": False,
        "iss": "https://auth.headspace.com/",
        "aud": "some_test_aud",
        # issued at
        "iat": mock_issued_at.timestamp(),
        # Expires at
        "exp": mock_expires_at.timestamp(),
        "sub": "auth0|some_test_sub",
    }
    yield jwt.encode(_t, JWT_SECRET, algorithm="HS256")


@pytest.fixture
def mock_invalid_id_token(mock_username, mock_issued_at, mock_expires_at):
    """Create an id token that's missing the required 'hsId' field.
    Note, I arbitrarily left a few fields in here that are not required for the client to function.
    The ONE field we do need is 'hsId' and that's explicitly missing here.
    """

    _t = {
        "email": mock_username,
        "email_verified": False,
        "iss": "https://auth.headspace.com/",
    }
    yield jwt.encode(_t, JWT_SECRET, algorithm="HS256")


# # Record expiration time
# if "exp" not in _a:
#     _e = "access_token missing exp!"
#     log.debug(_e, decoded=_a)
#     raise ValueError(_e)
# self._auth_token_expires = datetime.utcfromtimestamp(_a["exp"])
# log.info("Authenticated until expiration", at=self._auth_token_expires)
# # TODO: create an async timer to refresh the token before it expires?
