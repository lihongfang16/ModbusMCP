"""Auditing datastore that logs all external Modbus read/write operations.

Wraps pymodbus's ModbusSequentialDataBlock, delegating all storage to super()
while intercepting getValues/setValues calls to record operations in an
audit log.

Address offset: ModbusDeviceContext.getValues() adds +1 to the address
before calling DataBlock.getValues(). This class receives the +1-adjusted
address and subtracts 1 when logging, so the user-facing address is correct.
"""

from datetime import datetime, timezone
from typing import List, Optional

from pymodbus.constants import ExcCodes
from pymodbus.datastore import ModbusSequentialDataBlock

from .alias_manager import AliasManager, RegisterType
from .models import LogEntry
from .operation_log import OperationLog


class AuditingDataBlock(ModbusSequentialDataBlock):
    """DataBlock that logs all external read/write operations.

    All storage operations are delegated to the parent
    ModbusSequentialDataBlock. This class only adds auditing.

    Args:
        address: Starting address of the datastore (passed to super).
        values: Initial values (passed to super).
        operation_log: Shared OperationLog instance to record LogEntry instances to.
        alias_manager: AliasManager for resolving register aliases.
        server_id: Identifier of the server this block belongs to.
        register_type: The Modbus register type this block represents.
    """

    def __init__(
        self,
        address: int,
        values: list,
        operation_log: OperationLog,
        alias_manager: AliasManager,
        server_id: str,
        register_type: RegisterType,
    ) -> None:
        super().__init__(address, values)
        self.operation_log = operation_log
        self.alias_manager = alias_manager
        self.server_id = server_id
        self.register_type = register_type

    def getValues(self, address: int, count: int = 1):
        """Read values and log the operation.

        Steps:
            1. Delegate to super().getValues()
            2. If ILLEGAL_ADDRESS, return immediately (no logging)
            3. Log with user-facing address (address - 1)
            4. Resolve alias
            5. Append LogEntry to operation_log
        """
        result = super().getValues(address, count)
        if isinstance(result, ExcCodes):
            return result

        user_address = address - 1
        _, alias = self.alias_manager.resolve(
            self.server_id, self.register_type, user_address
        )

        entry = LogEntry(
            timestamp=datetime.now(timezone.utc).isoformat(),
            server_id=self.server_id,
            register_type=self.register_type,
            address=user_address,
            operation="get",
            source="external",
            count=count,
            alias=alias,
            new_value=list(result),
        )
        self.operation_log.add(entry)
        return result

    def setValues(self, address: int, values):
        """Write values and log the operation.

        Steps:
            1. Read old values via super().getValues()
            2. Delegate to super().setValues()
            3. If ILLEGAL_ADDRESS, return immediately (no logging)
            4. Log with user-facing address (address - 1)
            5. Resolve alias
            6. Append LogEntry with old and new values
        """
        if not isinstance(values, list):
            values = [values]
        old = super().getValues(address, count=len(values))
        result = super().setValues(address, values)
        if isinstance(result, ExcCodes):
            return result

        user_address = address - 1
        _, alias = self.alias_manager.resolve(
            self.server_id, self.register_type, user_address
        )

        entry = LogEntry(
            timestamp=datetime.now(timezone.utc).isoformat(),
            server_id=self.server_id,
            register_type=self.register_type,
            address=user_address,
            operation="set",
            source="external",
            count=len(values),
            alias=alias,
            old_value=list(old) if not isinstance(old, ExcCodes) else None,
            new_value=list(values),
        )
        self.operation_log.add(entry)
        return result

    def mcp_set(self, address: int, values: list) -> None | ExcCodes:
        """Write values from MCP (not external) and log the operation.

        Similar to setValues but logs with source='mcp' instead of
        'external'. Used when the MCP server itself writes to the
        datastore rather than an external Modbus client.

        Steps:
            1. Read old values
            2. Delegate to super().setValues()
            3. If ILLEGAL_ADDRESS, return immediately (no logging)
            4. Log with source='mcp'
        """
        if not isinstance(values, list):
            values = [values]
        old = super().getValues(address, count=len(values))
        result = super().setValues(address, values)
        if isinstance(result, ExcCodes):
            return result

        user_address = address - 1
        _, alias = self.alias_manager.resolve(
            self.server_id, self.register_type, user_address
        )

        entry = LogEntry(
            timestamp=datetime.now(timezone.utc).isoformat(),
            server_id=self.server_id,
            register_type=self.register_type,
            address=user_address,
            operation="set",
            source="mcp",
            count=len(values),
            alias=alias,
            old_value=list(old) if not isinstance(old, ExcCodes) else None,
            new_value=list(values),
        )
        self.operation_log.add(entry)
        return result
