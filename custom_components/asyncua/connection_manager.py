"""Persistent OPC-UA connection manager using Singleton pattern."""
from __future__ import annotations

import asyncio
import logging
from typing import Any

from asyncua import Client

_LOGGER = logging.getLogger("asyncua")


class OPCUAConnectionManager:
    """Singleton connection manager for OPC-UA servers."""

    _instances: dict[str, OPCUAConnectionManager] = {}
    _lock = asyncio.Lock()

    def __new__(cls, url: str) -> OPCUAConnectionManager:
        """Ensure one connection per URL (Singleton per server)."""
        if url not in cls._instances:
            instance = super().__new__(cls)
            cls._instances[url] = instance
        return cls._instances[url]

    def __init__(
        self,
        url: str,
        username: str | None = None,
        password: str | None = None,
        timeout: float = 5,
    ) -> None:
        """Initialize connection manager."""
        # Only initialize once per URL
        if hasattr(self, "_initialized"):
            return

        self._initialized = True
        self._url = url
        self._username = username
        self._password = password
        self._timeout = timeout
        self._client: Client | None = None
        self._is_connected: bool = False
        self._reference_count: int = 0

    @property
    def url(self) -> str:
        """Return the OPC-UA server URL."""
        return self._url

    @property
    def client(self) -> Client | None:
        """Return the OPC-UA client."""
        return self._client

    @property
    def is_connected(self) -> bool:
        """Return connection status."""
        return self._is_connected

    async def connect(self) -> bool:
        """Establish connection to OPC-UA server."""
        async with self._lock:
            if self._is_connected:
                _LOGGER.debug("Already connected to %s", self._url)
                self._reference_count += 1
                return True

            try:
                self._client = Client(url=self._url, timeout=self._timeout)
                self._client.secure_channel_timeout = 60000  # 1 minute
                self._client.session_timeout = 60000  # 1 minute

                if self._username is not None:
                    self._client.set_user(username=self._username)
                if self._password is not None:
                    self._client.set_password(pwd=self._password)

                await self._client.connect()
                self._is_connected = True
                self._reference_count = 1
                _LOGGER.info("Connected to OPC-UA server at %s", self._url)
                return True

            except Exception as e:
                _LOGGER.error("Failed to connect to %s: %s", self._url, e)
                self._is_connected = False
                self._client = None
                return False

    async def disconnect(self) -> bool:
        """Disconnect from OPC-UA server."""
        async with self._lock:
            self._reference_count = max(0, self._reference_count - 1)

            if self._reference_count > 0:
                _LOGGER.debug(
                    "Reference count for %s: %d, keeping connection open",
                    self._url,
                    self._reference_count,
                )
                return True

            try:
                if self._client is not None:
                    await self._client.disconnect()
                    _LOGGER.info("Disconnected from OPC-UA server at %s", self._url)
            except Exception as e:
                _LOGGER.error("Error disconnecting from %s: %s", self._url, e)
            finally:
                self._is_connected = False
                self._client = None
                self._reference_count = 0

            return True

    async def get_node_value(self, nodeid: str) -> Any:
        """Get value from a node."""
        if not self._is_connected or self._client is None:
            raise RuntimeError(f"Not connected to {self._url}")

        try:
            node = self._client.get_node(nodeid=nodeid)
            return await node.read_value()
        except Exception as e:
            _LOGGER.error("Error reading node %s: %s", nodeid, e)
            raise

    async def set_node_value(self, nodeid: str, value: Any) -> bool:
        """Set value to a node."""
        if not self._is_connected or self._client is None:
            raise RuntimeError(f"Not connected to {self._url}")

        try:
            node = self._client.get_node(nodeid=nodeid)
            await node.write_value(value)
            return True
        except Exception as e:
            _LOGGER.error("Error writing node %s: %s", nodeid, e)
            raise

    async def reconnect(self) -> bool:
        """Reconnect to the server."""
        _LOGGER.info("Attempting to reconnect to %s", self._url)
        await self.disconnect()
        await asyncio.sleep(1)  # Wait before reconnecting
        return await self.connect()

    def connection_state(self) -> str:
        """Return the connection state as string."""
        return "Connected" if self._is_connected else "Disconnected"

    @classmethod
    def get_instance(cls, url: str) -> OPCUAConnectionManager | None:
        """Get existing instance for URL if it exists."""
        return cls._instances.get(url)

    @classmethod
    def get_all_connections(cls) -> dict[str, OPCUAConnectionManager]:
        """Get all active connection instances."""
        return cls._instances.copy()
