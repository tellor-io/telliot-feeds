from __future__ import annotations

from typing import Any

from web3 import AsyncWeb3 as _AsyncWeb3


class AsyncWeb3Shim:
    """
    Compatibility shim around web3.AsyncWeb3 to ignore deprecated 'middlewares' kwarg.

    Some dependencies (e.g., multicall<=0.12.x) instantiate AsyncWeb3 with
    a 'middlewares' keyword argument, which is no longer accepted in web3 v7.
    This shim discards that argument while preserving all other behavior.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        # Drop deprecated kwarg if present
        kwargs.pop("middlewares", None)
        self._inner = _AsyncWeb3(*args, **kwargs)

    def __getattr__(self, name: str) -> Any:  # delegate attributes
        return getattr(self._inner, name)

    def __setattr__(self, name: str, value: Any) -> None:
        if name == "_inner":
            super().__setattr__(name, value)
        else:
            setattr(self._inner, name, value)
