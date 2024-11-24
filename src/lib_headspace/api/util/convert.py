"""Utils"""

import json
import re


def env_js_to_python(js_text: str):
    """Converts JavaScript object notation to Python dictionary.
    Meant for use with the env.js file that Headspace uses to ship configuration.
    If all goes well, env.js will look like this:

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
        sentry: 'https://1c5e633ac9274fdabc9a8119a59d7183@o28532.ingest.sentry.io/1500794',
    };

    document.getElementById('env_config').remove();

    And we'll turn that into a regular Python object.
    """

    # Remove the `window.<variable>` assignment
    js_text = re.sub(r"window\.\w+\s*=\s*", "", js_text)

    # Remove DOM manipulation
    js_text = re.sub(r"document\.getElementById\(.*?\);", "", js_text)

    # Remove trailing semicolon
    js_text = re.sub(r";\s*$", "", js_text.strip())

    # Replace JavaScript syntax with Python/JSON-compatible syntax
    ##
    # Replace single quotes with double quotes
    js_text = js_text.replace("'", '"')

    # # Add double quotes to keys
    js_text = re.sub(r"(?<=[{,])\s*(\w+)\s*:", r'"\1":', js_text)

    # Replace backticks with double quotes
    js_text = js_text.replace("`", '"')

    # Remove trailing commas before closing braces
    js_text = re.sub(r",\s*}", "}", js_text)

    return json.loads(js_text)
