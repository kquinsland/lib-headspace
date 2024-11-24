# lib-headspace

> [!NOTE]
> **This library is not affiliated with Headspace in any way.**
>
> I have reverse-engineered the API and it could change, and thus break this library, at any time.

This is a simple library to interact with the (private) Headspace API.

It is meant for _reading_ data; **writing** data or **accessing the audio** content is not supported and likely never will be.

## Using the library

See [demos/readme.md](demos/readme.md) for a quick start guide.

## Dev

[`uv`](https://docs.astral.sh/uv/) is used as a replacement for `poetry`.
[Install](https://docs.astral.sh/uv/getting-started/installation/) `uv` first and then it's quick/easy to get going:

```shell
# Note: Yes, this really does need 3.13!
❯ uv venv --python=3.13
Using CPython 3.13.0
Creating virtual environment at: .venv
Activate with: source .venv/bin/activate
# Install dependencies; consider --group=dev
❯ uv sync
Resolved 21 packages in 13ms
<...>
 + pycparser==2.22
 + pyjwt==2.10.0
 + pytest==8.3.3
 + ruff==0.7.4
 + structlog==24.4.0
 + yarl==1.18.0
```

### .pre-commit

`uv` will have taken care of installing [pre-commit](https://pre-commit.com/) if you used `uv sync --group=dev` to install dev dependencies.

As long as `pre-commit` is in your `$PATH`, connecting it to `git` is simple:

```shell
❯ pre-commit install
pre-commit installed at .git/hooks/pre-commit
```

You can run `pre-commit run --all-files` to lint and format your code.

> [!NOTE] The first time you run `pre-commit`, it will take a while to download and install the hooks.

```shell
❯ pre-commit run --all-files
[INFO] Initializing environment for https://github.com/pre-commit/pre-commit-hooks.
[INFO] Initializing environment for https://github.com/astral-sh/ruff-pre-commit.
[INFO] Installing environment for https://github.com/pre-commit/pre-commit-hooks.
[INFO] Once installed this environment will be reused.
[INFO] This may take a few minutes...
```

## TODO

- [ ] Tests for the client; currently could use a bit of a refactor.
- [ ] GHA automations
  - [ ] Automation to clean up old GHA runs
