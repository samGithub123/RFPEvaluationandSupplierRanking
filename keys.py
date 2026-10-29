# -*- coding: utf-8 -*-
"""
keys.py - API key / configuration loader for the RFP Evaluation project.

What it is for:
    Load the OpenAI API key from a folder-local `.env` file so that no
    secret is hardcoded in source. Mirrors the convention used by
    `exercises/miniProj/Shared/keys.py`.

What it does:
    ✅ Loads a `.env` file placed next to this script.
    ✅ Exposes `OPENAI_API_KEY`.
    ✅ Mirrors the key back into `os.environ` so the OpenAI / LangChain
       SDKs can pick it up automatically.
    ✅ Provides `require()` to fail with a clear message when the key is
       missing.

Setup:
    1. Copy `.env.example` to `.env` in this same folder.
    2. Add your key, e.g.:

        OPENAI_API_KEY=sk-...

    3. Never commit the `.env` file (it is ignored via the local .gitignore).

Requires: pip install python-dotenv
"""

import os

from dotenv import load_dotenv

# Load variables from a `.env` file placed next to this script (if it exists).
# override=True so this folder's `.env` always wins over a stray same-named
# variable that may already be set in the shell/system environment.
_ENV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
load_dotenv(_ENV_PATH, override=True)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Many SDKs (OpenAI, LangChain) pick up credentials automatically from the
# environment, so mirror whatever we found back into os.environ.
if OPENAI_API_KEY:
    os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY


def require(key_name: str, value: str) -> str:
    """Raise a helpful error if a required key was not found in the environment."""
    if not value:
        raise RuntimeError(
            f"{key_name} is not set. Add it to the .env file in "
            f"{os.path.dirname(os.path.abspath(__file__))} or export it as an "
            "environment variable before running this script."
        )
    return value
