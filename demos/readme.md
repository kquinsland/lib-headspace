# Quick demos for the api client

## Credentials

You will need to provide your own credentials to use the client.
The easiest way to do this is with [`direnv`](https://direnv.net/) via the `.envrc` file.

```shell
❯ cp .envrc.example .envrc
# Edit .envrc with your own credentials
❯ $EDITOR .envrc
# Tell direnv to load the new environment variables
❯ direnv allow
# Confirm the environment variables are set
❯ env | grep HEADSPACE
LIB_HEADSPACE_USERNAME=bobby.tables@gmail.com
LIB_HEADSPACE_PASSWORD=secretSquirrel123
```

## `poc.py`

This is a simple proof of concept script that shows how to use the client to authenticate and fetch user stats.
I have (lightly) redacted the output to protect my own privacy but the script should work for you as well.

The log ouptput should make it reasonably clear what's going on; some additional details about the auth/api calls are in the code and the [`docs/api/readme.md`](../docs/api/readme.md) file.

```shell
❯ ./poc.py
2024-11-24 14:58:25 [info     ] Lib-headspace PoC!
2024-11-24 14:58:25 [info     ] Got credentials                user=bobby.tables@gmail.com
2024-11-24 14:58:25 [info     ] Client created and credentials set. Attempting to get auth0 token...
2024-11-24 14:58:25 [debug    ] got data                       js_text=window.HEADSPACE_APP_CONFIG = {
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

2024-11-24 14:58:25 [debug    ] we have a valid env.js?        env={'auth0': {'authEnvironment': 'production', 'clientId': 'xkQY1I0RgfxPhCNtJZ70cd8oTzymDT1r', 'cookieConfig': {'domain': '.headspace.com', 'expires': 1, 'name': 'hsngjwt', 'path': '/', 'secure': False}, 'databaseConnection': 'User-Password-Headspace', 'domain': 'auth.headspace.com', 'enableCookieBackwardsCompatability': True, 'enableUserProfileManagement': True, 'pathToIconSprites': '/static/icons.svg', 'pathToLoginScreen': '/login', 'pathToRequiredUserProfileFieldsCollectionForm': '/missing-profile-fields', 'redirectWhenMissingRequiredUserProfileFields': True, 'requiredUserProfileFields': ['firstName', 'lastName']}, 'hosts': {'b2bWebsite': 'https://work.headspace.com', 'checkoutWebsite': 'https://checkout.headspace.com', 'headspaceApi': 'https://api.prod.headspace.com', 'headspaceContent': 'https://content.headspace.com', 'myHeadspace': 'https://my.headspace.com', 'reactWebsite': 'https://www.headspace.com', 'webviews': 'https://webviews.headspace.com'}, 'mParticleEnvironment': 'production', 'sentry': 'https://1c5e633ac9274fdabc9a8119a59d7183@o28532.ingest.sentry.io/1500794'}
2024-11-24 14:58:25 [debug    ] auth0.clientId discovered!     client_id=xkQY1I0RgfxPhCNtJZ70cd8oTzymDT1r
2024-11-24 14:58:25 [info     ] Attempting to log in...
2024-11-24 14:58:25 [debug    ] do_post_request                data={'realm': 'User-Password-Headspace', 'audience': 'https://api.prod.headspace.com', 'client_id': 'xkQY1I0RgfxPhCNtJZ70cd8oTzymDT1r', 'scope': 'openid email', 'grant_type': 'http://auth0.com/oauth/grant-type/password-realm', 'username': 'bobby.tables@gmail.com', 'password': 'secretSquirrel123'}
2024-11-24 14:58:26 [debug    ] access_token discovered!       access_token=eyJhbGciOiJSUzI1NiIsInR<... about 1150 characters omitted ...>eobr0UlQ1IzbpQoPyHJXdQJZE7qZc5w
2024-11-24 14:58:26 [debug    ] hsId discovered!               hs_id=HSUSER_SomeLongStringHere
2024-11-24 14:58:26 [info     ] Authenticated at               at=datetime.datetime(2024, 11, 24, 22, 58, 26, tzinfo=datetime.timezone.utc)
2024-11-24 14:58:26 [info     ] Authenticated until expiration at=datetime.datetime(2024, 11, 25, 22, 58, 26, tzinfo=datetime.timezone.utc)
2024-11-24 14:58:26 [info     ] Logged in successfully!
2024-11-24 14:58:26 [info     ] Fetching user stats...
2024-11-24 14:58:26 [info     ] Stats fetched                  count=5
2024-11-24 14:58:26 [info     ] Stat                           as_of=1984-01-01T01:23:45.000Z current=9001 label=TOTAL_SESSIONS previous=9000
2024-11-24 14:58:26 [info     ] Stat                           as_of=1984-01-01T01:23:45.000Z current=123 label=HIGHEST_RUN_STREAK previous=23
2024-11-24 14:58:26 [info     ] Stat                           as_of=1984-01-01T01:23:45.000Z current=3 label=RUN_STREAK previous=2
2024-11-24 14:58:26 [info     ] Stat                           as_of=1984-01-01T01:23:45.000Z current=6942 label=TOTAL_MINUTES previous=1234
2024-11-24 14:58:26 [info     ] Stat                           as_of=1984-01-01T01:23:45.000Z current=54 label=AVERAGE_MINUTES previous=69
```
