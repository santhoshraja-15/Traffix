"""
Lightweight in-process pub/sub event bus.

Components publish named events; subscribers register callbacks.
Keeps the core modules decoupled without requiring an external broker.
"""
from __future__ import annotations

import asyncio
from collections import defaultdict
from typing import Any, Callable, Coroutine, Dict, List

from app.utils.logging import get_logger

logger = get_logger(__name__)

# Callback type: either a plain callable or an async coroutine function.
Handler = Callable[..., Any]


class EventManager:
    """Async-compatible pub/sub event manager."""

    def __init__(self) -> None:
        self._handlers: Dict[str, List[Handler]] = defaultdict(list)

    def subscribe(self, event: str, handler: Handler) -> None:
        """Register *handler* to be called when *event* is published."""
        self._handlers[event].append(handler)
        logger.debug("Subscribed %s to event '%s'", handler, event)

    def unsubscribe(self, event: str, handler: Handler) -> None:
        handlers = self._handlers.get(event, [])
        try:
            handlers.remove(handler)
        except ValueError:
            pass

    async def publish(self, event: str, **kwargs: Any) -> None:
        """
        Publish *event* to all registered handlers.

        Async handlers are awaited; sync handlers are called directly.
        Errors in individual handlers are logged but do not abort others.
        """
        for handler in list(self._handlers.get(event, [])):
            try:
                result = handler(**kwargs)
                if asyncio.iscoroutine(result):
                    await result
            except Exception as exc:  # noqa: BLE001
                logger.error("Handler %s for event '%s' raised: %s", handler, event, exc)


# Module-level singleton.
event_manager = EventManager()
