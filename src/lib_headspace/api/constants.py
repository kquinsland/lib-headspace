"""
Constants
"""

from . import __version__ as version

APP_URL_BASE = "my.headspace.com"
AUTH_URL = "https://auth.headspace.com/oauth/token"
APP_ENV_JS_URL = f"https://{APP_URL_BASE}/env.js"
VERSION = version
API_URL_BASE = "https://api.prod.headspace.com"
APP_STATS_URL_BASE = f"{API_URL_BASE}/content/v1/user-stats"
