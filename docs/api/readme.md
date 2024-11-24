# Headspace API reverse engineering notes

Unfortunately, there is no public API documentation for Headspace.
Everything noted below comes from Firefox dev tools while interacting with the site.
I have redacted some of the output to protect my own privacy but you should be able to get the gist of what's going on.

## Auth

Intuitively, we first need to authenticate.
It seems that Headspace uses Auth0 for at least doing identity management.

```shell
❯ curl 'https://auth.headspace.com/oauth/token' --compressed -X POST \
-H 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:132.0) Gecko/20100101 Firefox/132.0' \
-H 'Accept: */*' \
-H 'Accept-Language: en-US,en;q=0.5' \
-H 'Accept-Encoding: gzip, deflate, br, zstd' \
-H 'Content-Type: application/json' \
-H 'Auth0-Client: eyJuYW1lIjoiYXV0aDAuanMiLCJ2ZXJzaW9uIjoiOS4xMy4yIn0=' \
-H 'Origin: https://www.headspace.com' \
-H 'Connection: keep-alive' \
-H 'Sec-Fetch-Dest: empty' \
-H 'Sec-Fetch-Mode: cors' \
-H 'Sec-Fetch-Site: same-site' \
-H 'Pragma: no-cache' \
-H 'Cache-Control: no-cache' \
-H 'TE: trailers' --data-raw '{"realm":"User-Password-Headspace","audience":"https://api.prod.headspace.com","client_id":"xkQY1I0RgfxPhCNtJZ70cd8oTzymDT1r","scope":"openid email","grant_type":"http://auth0.com/oauth/grant-type/password-realm","username":"bobby.tables@gmail.com","password":"secretSquirrel123"}'
```

That looks like pretty straightforward oAuth flow but there's a few unique things:

- `Auth0-Client` header. Not clear _where_ this comes from... Let's [dive deeper](#client_id).
  - Note that the `client_id` value in the payload is NOT the same as the `Auth0-Client` header!?
- `username` and `password` in the payload. We know how to get the values for these.

Taking a closer look at the `Auth0-Client` header, we can see that it's probably not critical to the request:

```shell
❯ echo "eyJuYW1lIjoiYXV0aDAuanMiLCJ2ZXJzaW9uIjoiOS4xMy4yIn0="|base64 -d
{"name":"auth0.js","version":"9.13.2"}
```

But it _may_ be worth setting just so we're not "fingerprinting" our requests as being different from the browser.

### `client_id`

With some more investigation, we can see that the entire headspace app is JS heavy.
Very early on in it's lifecycle, there's a request that goes out to fetch an `env.js` file.
This appears to contain lots of "set at runtime" values, including the `client_id`:

```shell
❯ curl 'https://my.headspace.com/env.js' --compressed \
-H 'User-Agent: Mozilla/5.0 (X11; Linux x86_64; rv:131.0) Gecko/20100101 Firefox/131.0' \
-H 'Accept: */*' \
-H 'Accept-Language: en-US,en;q=0.5' \
-H 'Accept-Encoding: gzip, deflate, br, zstd' \
-H 'Connection: keep-alive' \
-H 'Referer: https://my.headspace.com/' \
-H 'Cookie: hsDeviceId=bd6b4ef6-{remainingUUIDv4ValueOmittedHere}; lang=en; countryCode=US; hsngjwt=eyJh<...about 1150 characters omitted...>xw' \
-H 'Sec-Fetch-Dest: script' \
-H 'Sec-Fetch-Mode: no-cors' \
-H 'Sec-Fetch-Site: same-origin' \
-H 'Priority: u=2' \
-H 'Pragma: no-cache' \
-H 'Cache-Control: no-cache' \
-H 'TE: trailers'
```

Will return a payload like:

```js
window.HEADSPACE_APP_CONFIG = {
  auth0: {
    authEnvironment: 'production',
    clientId: 'xkQY1I0RgfxPhCNtJZ70cd8oTzymDT1r',
    cookieConfig: {
      domain: '.headspace.com',
      expires: 1,
      name: 'hsngjwt',
      path: '/',
      secure: false,
    },
    databaseConnection: 'User-Password-Headspace',
    domain: 'auth.headspace.com',
    enableCookieBackwardsCompatability: true,
    enableUserProfileManagement: true,
    pathToIconSprites: `/static/icons.svg`,
    pathToLoginScreen: `/login`,
    pathToRequiredUserProfileFieldsCollectionForm: '/missing-profile-fields',
    redirectWhenMissingRequiredUserProfileFields: true,
    requiredUserProfileFields: ['firstName', 'lastName'],
  },
  hosts: {
    b2bWebsite: 'https://work.headspace.com',
    checkoutWebsite: 'https://checkout.headspace.com',
    headspaceApi: 'https://api.prod.headspace.com',
    headspaceContent: 'https://content.headspace.com',
    myHeadspace: 'https://my.headspace.com',
    reactWebsite: 'https://www.headspace.com',
    webviews: 'https://webviews.headspace.com',
  },
  mParticleEnvironment: 'production',
  sentry:
    'https://1c5e633ac9274fdabc9a8119a59d7183@o28532.ingest.sentry.io/1500794',
};

document.getElementById('env_config').remove();
```

It's not clear how often values in this file change; some of them are likely static or super long-lived.
I'd bet that `auth0.clientId` is one of those values but it's not worth hardcoding it.
If it's easy enough, I'll add support for fetching this value at runtime but also allow explicitly setting it if needed.

### actually useful `jwt`s

To interact with the headspace API, we need an auth token that comes in the form of a b64 encoded `jwt`.
Obtaining one of these `jwt`s requires the `auth0.clientId` value and a user's email/password.

```shell
❯ curl 'https://auth.headspace.com/oauth/token' --compressed -X POST \
-H 'User-Agent: Mozilla/5.0 (X11; Linux x86_64; rv:131.0) Gecko/20100101 Firefox/131.0' \
-H 'Accept: */*' \
-H 'Accept-Language: en-US,en;q=0.5' \
-H 'Accept-Encoding: gzip, deflate, br, zstd' \
-H 'Content-Type: application/json' \
-H 'Auth0-Client: eyJuYW1lIjoiYXV0aDAuanMiLCJ2ZXJzaW9uIjoiOS4xMy4yIn0=' \
-H 'Origin: https://www.headspace.com' \
-H 'Connection: keep-alive' \
-H 'Sec-Fetch-Dest: empty' \
-H 'Sec-Fetch-Mode: cors' \
-H 'Sec-Fetch-Site: same-site' \
-H 'Pragma: no-cache' \
-H 'Cache-Control: no-cache' \
-H 'TE: trailers' --data-raw '{"realm":"User-Password-Headspace","audience":"https://api.prod.headspace.com","client_id":"xkQY1I0RgfxPhCNtJZ70cd8oTzymDT1r","scope":"openid email","grant_type":"http://auth0.com/oauth/grant-type/password-realm","username":"bobby.tables@gmail.com","password":"secretSquirrel123"}'
```

That request will return a json payload with a few keys.
The critical ones are the `access_token` and - to a lesser extent - the `id_token`.

When run through a jwt decoder, the `access_token` will look like:

```shell
{
    'https://api.prod.headspace.com/hsId': 'HSUSER_someUUIDHere',
    'https://api.prod.headspace.com/connection': 'User-Password-Headspace',
    'https://api.prod.headspace.com/providerId': 'bobby.tables@gmail.com',
    'https://api.prod.headspace.com/hsPlatform': 'DESKTOP',
    'iss': 'https://auth.headspace.com/',
    'sub': 'auth0|5ebd8c03b6cb610cbabd99e1',
    'aud': [
        'https://api.prod.headspace.com',
        'https://b2c-prod-headspace.auth0.com/userinfo'
    ],
    'iat': 1732241234,
    'exp': 1732335678,
    'scope': 'openid email',
    'gty': 'password',
    'azp': 'xkQY1I0RgfxPhCNtJZ70cd8oTzymDT1r'
}
```

And the `id_token` will look like:

```shell
{
    'hsId': 'HSUSER_someUUIDHere',
    'email': 'bobby.tables@gmail.com',
    'email_verified': False,
    'iss': 'https://auth.headspace.com/',
    'aud': 'xkQY1I0RgfxPhCNtJZ70cd8oTzymDT1r',
    'iat': 1732241234,
    'exp': 1732335678,
    'sub': 'auth0|5ebd8c03b6cb610cbabd99e1'
}
```

The `access_token` is the one we'll use to [interact](#stats) with the API.

## Stats

Using the raw b64 encoded `access_token` from the previous step, we can now interact with the API:

```shell
❯ curl 'https://api.prod.headspace.com/content/v1/user-stats?userId=HSUSER_someUUIDHere' --compressed \
-H 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:132.0) Gecko/20100101 Firefox/132.0' \
-H 'Accept: */*, application/json, text/plain' \
-H 'Accept-Language: en-US,en;q=0.5' \
-H 'Accept-Encoding: gzip, deflate, br, zstd' \
-H 'authorization: Bearer eyJhb<...about 1200 chars omitted ...>NAg' \
-H 'hs-languagepreference: en-US' \
-H 'Origin: https://my.headspace.com' \
-H 'Connection: keep-alive' \
-H 'Referer: https://my.headspace.com/' \
-H 'Sec-Fetch-Dest: empty' \
-H 'Sec-Fetch-Mode: cors' \
-H 'Sec-Fetch-Site: same-site' \
-H 'TE: trailers' | jq -r
[
  {
    "currentValue": 9001,
    "validUntil": null,
    "id": 12345604,
    "label": "TOTAL_SESSIONS",
    "userId": "HSUSER_someUUIDHere",
    "previousValue": 9000,
    "deletedAt": null,
    "clientUpdatedAt": "1984-01-01T01:23:45.000Z",
    "createdAt": "1984-01-01T01:23:45.000Z",
    "updatedAt": "1984-01-01T01:23:45.000Z"
  },
  {
    "currentValue": 123,
    "validUntil": null,
    "id": 12345605,
    "label": "HIGHEST_RUN_STREAK",
    "userId": "HSUSER_someUUIDHere",
    "previousValue": 23,
    "deletedAt": null,
    "clientUpdatedAt": "1984-01-01T01:23:45.000Z",
    "createdAt": "1984-01-01T01:23:45.000Z",
    "updatedAt": "1984-01-01T01:23:45.000Z"
  },
  {
    "currentValue": 3,
    "validUntil": "1984-01-02T01:23:45.000Z",
    "id": 12345606,
    "label": "RUN_STREAK",
    "userId": "HSUSER_someUUIDHere",
    "previousValue": 2,
    "deletedAt": null,
    "clientUpdatedAt": "1984-01-01T01:23:45.000Z",
    "createdAt": "1984-01-01T01:23:45.000Z",
    "updatedAt": "1984-01-01T01:23:45.000Z"
  },
  {
    "currentValue": 6942,
    "validUntil": null,
    "id": 12345607,
    "label": "TOTAL_MINUTES",
    "userId": "HSUSER_someUUIDHere",
    "previousValue": 1234,
    "deletedAt": null,
    "clientUpdatedAt": "1984-01-01T01:23:45.000Z",
    "createdAt": "1984-01-01T01:23:45.000Z",
    "updatedAt": "1984-01-01T01:23:45.000Z"
  },
  {
    "currentValue": 54,
    "validUntil": null,
    "id": 12345608,
    "label": "AVERAGE_MINUTES",
    "userId": "HSUSER_someUUIDHere",
    "previousValue": 69,
    "deletedAt": null,
    "clientUpdatedAt": "1984-01-01T01:23:45.000Z",
    "createdAt": "1984-01-01T01:23:45.000Z",
    "updatedAt": "1984-01-01T01:23:45.000Z"
  }
]
```

A few observations:

- it looks like each 'stat' shares a common schema; they all feature `validUntil` but only one stat has a non-null value.
- The `createdAt` should be the same as account creation date but it'll be interesting to see if they add new stats or if anybody has an account that pre-dates some of these stats.
- I do not have a clue as to why they have a `clientUpdatedAt` _and_ a `updatedAt` field unless there's some sort of value in knowing when a stat actually changed versus when the record was updated.
  - The only thing that comes to mind immediately is using a mobile app while offline and then _later_ syncing up with the server?
- Each stat has a unique `id`. Does this map back to a row in a database? They do appear to be sequential but I don't know if other users have the same `id` values for their stats?!
