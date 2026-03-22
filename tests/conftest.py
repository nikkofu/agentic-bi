import inspect

import httpx


def _patch_httpx_client_for_starlette_testclient() -> None:
    if "app" in inspect.signature(httpx.Client.__init__).parameters:
        return

    original_init = httpx.Client.__init__

    def patched_init(self, *args, app=None, **kwargs):
        original_init(self, *args, **kwargs)

    httpx.Client.__init__ = patched_init


_patch_httpx_client_for_starlette_testclient()
