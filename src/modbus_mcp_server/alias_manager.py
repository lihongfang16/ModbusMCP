"""Alias management for Modbus register addresses.

Provides thread-safe alias resolution for register addresses keyed by
(server_id, register_type, address). This allows human-readable names
to be attached to numeric Modbus register addresses.
"""

import threading
from typing import Dict, List, Optional, Tuple

from .models import AliasEntry, RegisterType


class AliasManager:
    """Thread-safe manager for register address aliases.

    Maintains a mapping of (server_id, register_type, address) -> alias,
    allowing human-readable names for Modbus register addresses.

    The manager is fully thread-safe via threading.RLock, matching the
    concurrency pattern used elsewhere in the codebase.
    """

    def __init__(self) -> None:
        """Initialize an empty alias manager."""
        self._aliases: Dict[Tuple[str, RegisterType, int], str] = {}
        self._lock = threading.RLock()

    def set_alias(
        self,
        server_id: str,
        register_type: RegisterType,
        address: int,
        alias: str,
    ) -> None:
        """Set or overwrite an alias for a register address.

        Args:
            server_id: The server instance identifier.
            register_type: The Modbus register type.
            address: The numeric register address.
            alias: The human-readable alias name.
        """
        with self._lock:
            self._aliases[(server_id, register_type, address)] = alias

    def get_alias(
        self,
        server_id: str,
        register_type: RegisterType,
        address: int,
    ) -> Optional[str]:
        """Retrieve the alias for a register address, if any.

        Args:
            server_id: The server instance identifier.
            register_type: The Modbus register type.
            address: The numeric register address.

        Returns:
            The alias string if set, otherwise None.
        """
        with self._lock:
            return self._aliases.get((server_id, register_type, address))

    def list_aliases(
        self,
        server_id: Optional[str] = None,
    ) -> List[AliasEntry]:
        """List all alias entries, optionally filtered by server.

        Args:
            server_id: If provided, only return aliases for this server.
                       If None, return all aliases across all servers.

        Returns:
            A list of AliasEntry dataclass instances.
        """
        with self._lock:
            if server_id is None:
                return [
                    AliasEntry(server_id=sid, register_type=rt, address=addr, alias=alias_key)
                    for (sid, rt, addr), alias_key in self._aliases.items()
                ]
            return [
                AliasEntry(server_id=sid, register_type=rt, address=addr, alias=alias_key)
                for (sid, rt, addr), alias_key in self._aliases.items()
                if sid == server_id
            ]

    def clear_aliases(self, server_id: str) -> None:
        """Remove all aliases for a given server.

        Args:
            server_id: The server whose aliases should be removed.
        """
        with self._lock:
            keys_to_remove = [
                key for key in self._aliases if key[0] == server_id
            ]
            for key in keys_to_remove:
                del self._aliases[key]

    def resolve(
        self,
        server_id: str,
        register_type: RegisterType,
        address: int,
    ) -> Tuple[int, Optional[str]]:
        """Resolve an address to its alias, returning both.

        This is a convenience method that always returns the original
        address along with the alias (if one exists). Useful for
        display/logging where the alias replaces the raw address.

        Args:
            server_id: The server instance identifier.
            register_type: The Modbus register type.
            address: The numeric register address.

        Returns:
            A tuple of (address, alias_string_or_None).
        """
        with self._lock:
            alias = self._aliases.get((server_id, register_type, address))
            return address, alias
