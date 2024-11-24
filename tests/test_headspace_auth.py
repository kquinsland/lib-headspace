"""Some tests for the HeadSpace API client.
There are two main flows that we need to test:

- Fetching the auth0 client ID (TODO: in another file...)
- Fetching the auth token
"""

import jwt
import pytest

from src.lib_headspace.api.client import HeadSpace
from src.lib_headspace.api.constants import AUTH_URL


##
# Test basic auth token retrieval
##
# First, check that we get a ValueError if the auth0 client id, username, password are not set
@pytest.mark.asyncio
async def test_value_error_on_attempted_auth_with_no_required_values_set(
    mock_aioresponse, mock_auth0_client_id, mock_username, mock_password
):
    client = HeadSpace()
    with pytest.raises(ValueError) as e:
        await client.get_headspace_auth_token()
    assert str(e.value) == "Can't get headspace auth if auth0_client_id is not set!"

    # Ok, set the auth0 client id and try again
    client.auth0_client_id = mock_auth0_client_id
    with pytest.raises(ValueError) as e:
        await client.get_headspace_auth_token()
    assert str(e.value) == "Can't get headspace auth if user_name is not set!"

    # Set both the auth0 client id and the username, but not the password
    client.user_name = mock_username
    with pytest.raises(ValueError) as e:
        await client.get_headspace_auth_token()
    assert str(e.value) == "Can't get headspace auth if password is not set!"


# Ok, we're sure that missing values will throw a value error. Let's test handling replies
# TODO: this should probably be broken up into multiple tests since we have a non-trivial matrix of things
#   that we're testing / a variety of ways that the auth response could be broken:
#   - Missing tokens in the reply
#   - Tokens present but corrupted / not parsable
#   - Tokens present but missing required fields
#   - All tokens there and parsable but there's something fishy about the date(s) they're
#       valid for
#           - Issued in the future
#           - Expired already
@pytest.mark.asyncio
async def test_value_error_thrown_on_broken_reply(
    mock_aioresponse,
    mock_auth0_client_id,
    mock_username,
    mock_password,
    mock_invalid_id_token,
    mock_invalid_access_token,
):
    """
    Nominally, an auth request would return a JSON object with the keys:
        ['access_token', 'id_token', 'scope', 'expires_in', 'token_type']
    Of those, everything we need can be parsed out of the ID/Access tokens so that's what we require.
    """
    # Set up client w/ required values
    client = HeadSpace()
    client.auth0_client_id = mock_auth0_client_id
    client.user_name = mock_username
    client.password = mock_password

    # If either access or id token is missing, ValueError should be raised
    missing_id_token_response = {
        "access_token": "test_access_token",
    }

    mock_aioresponse.post(AUTH_URL, payload=missing_id_token_response)
    with pytest.raises(ValueError) as e:
        await client.get_headspace_auth_token()

    missing_access_token_response = {
        "id_token": "test_id_token",
    }
    mock_aioresponse.post(AUTH_URL, payload=missing_access_token_response)
    with pytest.raises(ValueError) as e:
        await client.get_headspace_auth_token()
    assert str(e.value) == "Auth response missing access_token!"

    # If both tokens are present, but either is invalid, a DecodeError should be raised
    complete_but_invalid_response = {
        "access_token": "test_access_token",
        "id_token": "test_id_token",
    }
    mock_aioresponse.post(AUTH_URL, payload=complete_but_invalid_response)
    with pytest.raises(jwt.exceptions.DecodeError) as e:
        await client.get_headspace_auth_token()

    # Lastly, test that the properly decoded jwt contains the required fields
    complete_but_subtly_invalid_response = {
        "access_token": mock_invalid_access_token,
        "id_token": mock_invalid_id_token,
    }
    mock_aioresponse.post(AUTH_URL, payload=complete_but_subtly_invalid_response)
    with pytest.raises(ValueError) as e:
        await client.get_headspace_auth_token()
    assert str(e.value) == "id_token missing hsId!"


# Test that we handle a valid response correctly
@pytest.mark.asyncio
async def test_valid_auth_reply(
    mock_aioresponse,
    mock_auth0_client_id,
    mock_username,
    mock_password,
    mock_valid_access_token,
    mock_valid_id_token,
    mock_issued_at,
    mock_expires_at,
    mock_headspace_user_id,
):
    """
    Nominally, an auth request would return a JSON object with the keys:
        ['access_token', 'id_token', 'scope', 'expires_in', 'token_type']
    Of those, everything we need can be parsed out of the ID/Access tokens so that's what we require.
    """
    valid_auth = {
        "access_token": mock_valid_access_token,
        "id_token": mock_valid_id_token,
        # These values do not matter...
        "scope": "openid email",
        "expires_in": 3600,
        "token_type": "Bearer",
    }
    # Set up client w/ required values
    client = HeadSpace()
    client.auth0_client_id = mock_auth0_client_id
    client.user_name = mock_username
    client.password = mock_password

    mock_aioresponse.post(AUTH_URL, payload=valid_auth)
    await client.get_headspace_auth_token()
    # If the auth token was fetched/parsed correctly, we should have the internal headspace user ID
    #   and an auth token and expiration time set
    assert client.expiration == mock_expires_at
    assert client._auth_token == mock_valid_access_token
    assert client.hs_id == mock_headspace_user_id


# @pytest.mark.asyncio
# async def test_valid_reply(mock_aioresponse, mock_auth0_jwt):
#     # Assume we get back a valid reply. We care that the reply has
#     #   ['access_token', 'id_token',  'expires_in']
#     reply = {
#         "access_token": mock_auth0_jwt,
#         "id_token": "test_id_token",
#         "expires_in": 100,
#     }
#     mock_aioresponse.post(AUTH_URL, payload=reply)
#     client = HeadSpace()
#     client.auth0_client_id = "test_client_id"
#     # TODO: setter on the Auth0client ID so I can mock that here.
#     # This will fail because we're not mocking a bunch of JWT stuff
#     # I should just make valid JWTs to test with / load from a file in a test fixture
#     resp = await client.get_headspace_auth_token()


# TODO: build tests for the auth0ClientID fetch process. We already have tests for the parse bit so it should just be as simple as instantiating a client
#   and not setting the clientid and then calling the method that fetches it and checking that the request went out. We already know that a valid response
#   will be parsed correctly....
