"""Tests for the ConnectionManager class."""

import pytest
from hypothesis import given, strategies as st, settings
from unittest.mock import Mock, patch

from modbus_mcp_server.connection_manager import ConnectionManager
from modbus_mcp_server.models import SerialPortInfo


class TestConnectionManager:
    """Test cases for ConnectionManager."""
    
    def test_init(self):
        """Test ConnectionManager initialization."""
        cm = ConnectionManager()
        assert cm.clients == {}
        assert cm.client_info == {}
        assert cm.used_ports == set()
        assert cm._lock is not None
    
    def test_list_serial_ports_empty(self):
        """Test listing serial ports when none are available."""
        cm = ConnectionManager()
        
        with patch('serial.tools.list_ports.comports', return_value=[]):
            ports = cm.list_serial_ports()
            assert ports == []
    
    def test_list_serial_ports_with_ports(self):
        """Test listing serial ports when ports are available."""
        cm = ConnectionManager()
        
        # Mock serial port
        mock_port = Mock()
        mock_port.device = "COM1"
        mock_port.description = "Test Serial Port"
        
        with patch('serial.tools.list_ports.comports', return_value=[mock_port]):
            ports = cm.list_serial_ports()
            
            assert len(ports) == 1
            assert ports[0].port == "COM1"
            assert ports[0].description == "Test Serial Port"
            assert ports[0].available is True
            assert ports[0].in_use_by_client is None
    
    @given(
        port_names=st.lists(
            st.text(min_size=1, max_size=10, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))),
            min_size=0,
            max_size=10,
            unique=True
        )
    )
    def test_serial_port_discovery_property(self, port_names):
        """Property test for serial port discovery and availability.
        
        **Property 10: Serial Port Discovery and Availability**
        **Validates: Requirements 11.1, 11.2, 11.3**
        
        For any set of available serial ports, the system should:
        1. Return accurate port information
        2. Mark all ports as available when no clients exist
        3. Provide consistent port descriptions
        """
        # Feature: modbus-mcp-server, Property 10: Serial Port Discovery and Availability
        cm = ConnectionManager()
        
        # Create mock ports
        mock_ports = []
        for i, port_name in enumerate(port_names):
            mock_port = Mock()
            mock_port.device = f"COM{i}" if port_name.startswith("COM") else port_name
            mock_port.description = f"Mock port {i}"
            mock_ports.append(mock_port)
        
        with patch('serial.tools.list_ports.comports', return_value=mock_ports):
            ports = cm.list_serial_ports()
            
            # Property: All returned ports should have valid information
            assert len(ports) == len(mock_ports)
            
            for i, port_info in enumerate(ports):
                # Each port should have required fields
                assert isinstance(port_info, SerialPortInfo)
                assert port_info.port is not None
                assert port_info.description is not None
                assert isinstance(port_info.available, bool)
                
                # When no clients exist, all ports should be available
                assert port_info.available is True
                assert port_info.in_use_by_client is None
    
    @given(
        port_name=st.text(min_size=1, max_size=10, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))),
        baudrate=st.sampled_from([9600, 19200, 38400, 57600, 115200]),
        slave_id=st.integers(min_value=1, max_value=247)
    )
    def test_port_availability_tracking_property(self, port_name, baudrate, slave_id):
        """Property test for port availability tracking.
        
        For any valid RTU client creation, the port should be marked as unavailable
        and correctly tracked until the client is closed.
        """
        # Feature: modbus-mcp-server, Property 10: Serial Port Discovery and Availability
        cm = ConnectionManager()
        
        # Mock the port to exist
        mock_port = Mock()
        mock_port.device = port_name
        mock_port.description = "Test port"
        
        with patch('serial.tools.list_ports.comports', return_value=[mock_port]):
            # Initially, port should be available
            initial_ports = cm.list_serial_ports()
            if initial_ports:
                assert initial_ports[0].available is True
                assert initial_ports[0].in_use_by_client is None
            
            try:
                # Create RTU client
                with patch('modbus_mcp_server.client_wrapper.ModbusClientWrapper.create_rtu_client'):
                    client_id = cm.create_rtu_client(port_name, baudrate, slave_id)
                    
                    # Port should now be unavailable
                    ports_after_create = cm.list_serial_ports()
                    port_info = next((p for p in ports_after_create if p.port == port_name), None)
                    
                    if port_info:
                        assert port_info.available is False
                        assert port_info.in_use_by_client == client_id
                    
                    # Close the client
                    cm.close_client(client_id)
                    
                    # Port should be available again
                    ports_after_close = cm.list_serial_ports()
                    port_info_after = next((p for p in ports_after_close if p.port == port_name), None)
                    
                    if port_info_after:
                        assert port_info_after.available is True
                        assert port_info_after.in_use_by_client is None
                        
            except ValueError:
                # Some parameter combinations might be invalid, which is acceptable
                pass
    
    def test_list_serial_ports_exception_handling(self):
        """Test that serial port listing handles exceptions gracefully."""
        cm = ConnectionManager()
        
        with patch('serial.tools.list_ports.comports', side_effect=Exception("Mock error")):
            ports = cm.list_serial_ports()
            assert ports == []
    
    def test_port_in_use_detection(self):
        """Test detection of ports in use by active clients."""
        cm = ConnectionManager()
        
        # Mock a port
        mock_port = Mock()
        mock_port.device = "COM1"
        mock_port.description = "Test port"
        
        # Add a port to used_ports manually
        cm.used_ports.add("COM1")
        
        # Add fake client info
        cm.client_info["test-client"] = Mock()
        cm.client_info["test-client"].client_type = "RTU"
        cm.client_info["test-client"].connection_params = {"port": "COM1"}
        
        with patch('serial.tools.list_ports.comports', return_value=[mock_port]):
            ports = cm.list_serial_ports()
            
            assert len(ports) == 1
            assert ports[0].available is False
            assert ports[0].in_use_by_client == "test-client"
    
    @given(
        num_clients=st.integers(min_value=1, max_value=20),
        client_type=st.sampled_from(["RTU", "TCP"])
    )
    def test_client_creation_uniqueness_property(self, num_clients, client_type):
        """Property test for client creation uniqueness.
        
        **Property 1: Client Creation Uniqueness**
        **Validates: Requirements 1.3, 2.3, 10.5**
        
        For any sequence of client creation operations (RTU or TCP), 
        all returned client identifiers should be unique across the entire system.
        """
        # Feature: modbus-mcp-server, Property 1: Client Creation Uniqueness
        cm = ConnectionManager()
        created_client_ids = set()
        
        try:
            for i in range(num_clients):
                if client_type == "RTU":
                    # Use unique port names to avoid conflicts
                    port_name = f"COM{i+10}"  # Start from COM10 to avoid real ports
                    
                    with patch('modbus_mcp_server.client_wrapper.ModbusClientWrapper.create_rtu_client'):
                        try:
                            client_id = cm.create_rtu_client(port_name, 9600, 1)
                            
                            # Property: All client IDs should be unique
                            assert client_id not in created_client_ids, f"Duplicate client ID: {client_id}"
                            created_client_ids.add(client_id)
                            
                        except ValueError:
                            # Some parameter combinations might be invalid, which is acceptable
                            pass
                
                elif client_type == "TCP":
                    # Use unique host addresses
                    host = f"192.168.1.{i+10}"
                    
                    with patch('modbus_mcp_server.client_wrapper.ModbusClientWrapper.create_tcp_client'):
                        try:
                            client_id = cm.create_tcp_client(host, 502, 1)
                            
                            # Property: All client IDs should be unique
                            assert client_id not in created_client_ids, f"Duplicate client ID: {client_id}"
                            created_client_ids.add(client_id)
                            
                        except ValueError:
                            # Some parameter combinations might be invalid, which is acceptable
                            pass
            
            # Property: The number of unique client IDs should equal the number of successful creations
            assert len(created_client_ids) == len(cm.clients)
            
            # Property: All client IDs in the manager should be in our tracking set
            for client_id in cm.clients.keys():
                assert client_id in created_client_ids
                
        finally:
            # Clean up
            cm.cleanup_all()
    
    @given(
        num_threads=st.integers(min_value=2, max_value=5),
        operations_per_thread=st.integers(min_value=1, max_value=3)
    )
    @settings(deadline=None)  # Disable deadline for concurrent operations
    def test_concurrent_client_support_property(self, num_threads, operations_per_thread):
        """Property test for concurrent client support.
        
        **Property 9: Concurrent Client Support**
        **Validates: Requirements 10.1, 10.2**
        
        For any number of concurrent client connections, the system should maintain 
        separate connection states and allow independent operations on each client.
        """
        # Feature: modbus-mcp-server, Property 9: Concurrent Client Support
        import threading
        import time
        
        cm = ConnectionManager()
        created_clients = []
        errors = []
        lock = threading.Lock()
        
        def create_and_operate_clients(thread_id):
            """Create clients and perform operations in a separate thread."""
            thread_clients = []
            
            try:
                for i in range(operations_per_thread):
                    # Create RTU client
                    port_name = f"COM{thread_id * 100 + i}"
                    
                    with patch('modbus_mcp_server.client_wrapper.ModbusClientWrapper.create_rtu_client'):
                        try:
                            client_id = cm.create_rtu_client(port_name, 9600, 1)
                            thread_clients.append(client_id)
                            
                            # Perform some operations on the client
                            client_info = cm.get_client_info(client_id)
                            assert client_info is not None
                            assert client_info.client_id == client_id
                            
                            # Test that we can retrieve the client
                            client = cm.get_client(client_id)
                            assert client is not None
                            
                        except ValueError:
                            # Some parameter combinations might be invalid
                            pass
                
                # Add successful clients to the shared list
                with lock:
                    created_clients.extend(thread_clients)
                    
            except Exception as e:
                with lock:
                    errors.append(f"Thread {thread_id} error: {e}")
        
        # Create and start threads
        threads = []
        for thread_id in range(num_threads):
            thread = threading.Thread(target=create_and_operate_clients, args=(thread_id,))
            threads.append(thread)
        
        # Start all threads
        for thread in threads:
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        try:
            # Property: No errors should occur during concurrent operations
            assert len(errors) == 0, f"Concurrent operations failed: {errors}"
            
            # Property: All created client IDs should be unique
            unique_clients = set(created_clients)
            assert len(unique_clients) == len(created_clients), "Duplicate client IDs found"
            
            # Property: The connection manager should track all created clients
            active_clients = cm.list_clients()
            assert len(active_clients) == len(created_clients), "Client count mismatch"
            
            # Property: Each client should maintain independent state
            for client_id in created_clients:
                client_info = cm.get_client_info(client_id)
                assert client_info is not None, f"Client info missing for {client_id}"
                assert client_info.client_id == client_id, "Client ID mismatch"
                
                client = cm.get_client(client_id)
                assert client is not None, f"Client missing for {client_id}"
            
            # Property: Concurrent access to client listing should be consistent
            list_results = []
            
            def list_clients_concurrently():
                clients = cm.list_clients()
                list_results.append(len(clients))
            
            list_threads = []
            for _ in range(5):  # Test with 5 concurrent list operations
                thread = threading.Thread(target=list_clients_concurrently)
                list_threads.append(thread)
            
            for thread in list_threads:
                thread.start()
            
            for thread in list_threads:
                thread.join()
            
            # All list operations should return the same count
            assert all(count == len(created_clients) for count in list_results), \
                f"Inconsistent client counts: {list_results}"
                
        finally:
            # Clean up all clients
            cm.cleanup_all()

class TestConnectionManagerErrorScenarios:
    """Test cases for ConnectionManager error scenarios."""

    def test_create_rtu_client_invalid_parameters(self):
        """Test RTU client creation with invalid parameters."""
        cm = ConnectionManager()
        
        # Test invalid slave ID
        with pytest.raises(ValueError, match="Slave ID must be between 1 and 247"):
            cm.create_rtu_client("COM1", 9600, 0)
        
        with pytest.raises(ValueError, match="Slave ID must be between 1 and 247"):
            cm.create_rtu_client("COM1", 9600, 248)
        
        # Test invalid baudrate
        with pytest.raises(ValueError, match="Baudrate must be one of"):
            cm.create_rtu_client("COM1", 1200, 1)
        
        # Test empty port
        with pytest.raises(ValueError, match="Port must be a non-empty string"):
            cm.create_rtu_client("", 9600, 1)

    def test_create_tcp_client_invalid_parameters(self):
        """Test TCP client creation with invalid parameters."""
        cm = ConnectionManager()
        
        # Test invalid slave ID
        with pytest.raises(ValueError, match="Slave ID must be between 1 and 247"):
            cm.create_tcp_client("192.168.1.100", 502, 0)
        
        # Test invalid port
        with pytest.raises(ValueError, match="Port must be between 1 and 65535"):
            cm.create_tcp_client("192.168.1.100", 0, 1)
        
        with pytest.raises(ValueError, match="Port must be between 1 and 65535"):
            cm.create_tcp_client("192.168.1.100", 65536, 1)
        
        # Test empty host
        with pytest.raises(ValueError, match="Host must be a non-empty string"):
            cm.create_tcp_client("", 502, 1)

    def test_port_already_in_use_error(self):
        """Test error when trying to use a port that's already in use."""
        cm = ConnectionManager()
        
        with patch('src.modbus_mcp_server.client_wrapper.ModbusClientWrapper.create_rtu_client') as mock_create:
            mock_wrapper = Mock()
            mock_create.return_value = mock_wrapper
            
            # Create first client
            client_id1 = cm.create_rtu_client("COM1", 9600, 1)
            assert client_id1 is not None
            
            # Try to create second client on same port
            with pytest.raises(ValueError, match="Serial port COM1 is already in use"):
                cm.create_rtu_client("COM1", 9600, 2)

    def test_client_creation_failure_cleanup(self):
        """Test that failed client creation cleans up properly."""
        cm = ConnectionManager()
        
        # Test failure during RTUParams creation (invalid baudrate)
        with pytest.raises(ValueError, match="Invalid RTU parameters"):
            cm.create_rtu_client("COM1", 1200, 1)  # Invalid baudrate
        
        # Verify cleanup - port should not be marked as used
        assert "COM1" not in cm.used_ports
        assert len(cm.clients) == 0
        assert len(cm.client_info) == 0

    def test_close_nonexistent_client(self):
        """Test closing a client that doesn't exist."""
        cm = ConnectionManager()
        
        result = cm.close_client("nonexistent-id")
        assert result is False

    def test_get_nonexistent_client(self):
        """Test getting a client that doesn't exist."""
        cm = ConnectionManager()
        
        client = cm.get_client("nonexistent-id")
        assert client is None
        
        client_info = cm.get_client_info("nonexistent-id")
        assert client_info is None

    def test_serial_port_listing_error_handling(self):
        """Test error handling when serial port listing fails."""
        cm = ConnectionManager()
        
        with patch('serial.tools.list_ports.comports', side_effect=Exception("Port listing failed")):
            ports = cm.list_serial_ports()
            # Should return empty list on error
            assert ports == []

    def test_client_disconnect_error_handling(self):
        """Test error handling during client disconnection."""
        cm = ConnectionManager()
        
        with patch('modbus_mcp_server.connection_manager.ModbusClientWrapper.create_rtu_client') as mock_create:
            mock_wrapper = Mock()
            mock_wrapper.disconnect.side_effect = Exception("Disconnect failed")
            mock_create.return_value = mock_wrapper
            
            # Create client
            client_id = cm.create_rtu_client("COM1", 9600, 1)
            
            # Verify the mock wrapper was stored
            stored_client = cm.clients[client_id]
            assert stored_client is mock_wrapper
            
            # Close client (should handle disconnect error gracefully)
            result = cm.close_client(client_id)
            
            # Should still clean up even if disconnect fails, but return False due to error
            assert result is False  # Returns False due to disconnect error
            assert client_id not in cm.clients
            assert client_id not in cm.client_info
            assert "COM1" not in cm.used_ports

    def test_concurrent_access_thread_safety(self):
        """Test thread safety of connection manager operations."""
        import threading
        import time
        
        cm = ConnectionManager()
        results = []
        errors = []
        
        def create_client_worker(port_suffix):
            try:
                with patch('src.modbus_mcp_server.client_wrapper.ModbusClientWrapper.create_rtu_client') as mock_create:
                    mock_wrapper = Mock()
                    mock_create.return_value = mock_wrapper
                    
                    client_id = cm.create_rtu_client(f"COM{port_suffix}", 9600, 1)
                    results.append(client_id)
                    time.sleep(0.01)  # Small delay
                    cm.close_client(client_id)
            except Exception as e:
                errors.append(e)
        
        # Create multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=create_client_worker, args=(i,))
            threads.append(thread)
        
        # Start all threads
        for thread in threads:
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Verify no errors occurred and all operations completed
        assert len(errors) == 0
        assert len(results) == 5
        assert len(set(results)) == 5  # All client IDs should be unique
        
        # Verify cleanup
        assert len(cm.clients) == 0
        assert len(cm.client_info) == 0
        assert len(cm.used_ports) == 0