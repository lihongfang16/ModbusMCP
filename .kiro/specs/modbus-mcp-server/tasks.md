# Implementation Plan: Modbus MCP Server

## Overview

This implementation plan breaks down the Modbus MCP Server development into discrete, manageable tasks. Each task builds incrementally toward a complete MCP server that exposes Modbus client functionality through fastMCP 2.0 and pymodbus.

## Tasks

- [x] 1. Set up project structure and dependencies
  - Create Python project with proper directory structure
  - Set up pyproject.toml with fastMCP and pymodbus dependencies
  - Configure development environment and basic project files
  - _Requirements: All requirements depend on proper project setup_

- [x] 2. Implement core data models and validation
  - [x] 2.1 Create data model classes for client info and results
    - Implement ClientInfo, ModbusResult, RTUParams, TCPParams dataclasses
    - Add proper type hints and validation methods
    - _Requirements: 1.1, 2.1, 10.2_

  - [x] 2.2 Write property test for data model validation
    - **Property 3: Invalid Parameter Rejection**
    - **Validates: Requirements 1.2, 2.2, 2.4, 1.5**

  - [x] 2.3 Implement ModbusValidator class
    - Create validation methods for slave IDs, addresses, register values
    - Implement IP address and port validation
    - Add descriptive error message generation
    - _Requirements: 1.5, 2.4, 8.4, 12.1, 12.4_

  - [x] 2.4 Write property test for address range validation
    - **Property 8: Address Range Validation**
    - **Validates: Requirements 4.4, 6.4, 7.4, 9.4, 12.4**

- [x] 3. Implement Modbus client wrapper
  - [x] 3.1 Create ModbusClientWrapper class
    - Implement wrapper around pymodbus RTU and TCP clients
    - Add connection state management and error handling
    - Implement unified interface for both client types
    - _Requirements: 1.1, 2.1, 3.1, 3.3_

  - [x] 3.2 Write property test for client lifecycle
    - **Property 4: Client Lifecycle Management**
    - **Validates: Requirements 3.1, 3.3, 3.4**

  - [x] 3.3 Implement read operations (coils, discrete inputs, registers)
    - Add methods for reading coils, discrete inputs, holding registers, input registers
    - Implement proper error handling and data format conversion
    - _Requirements: 4.1, 4.2, 6.1, 6.2, 7.1, 7.2, 9.1, 9.2_

  - [x] 3.4 Write property test for read operations
    - **Property 6: Read Operation Data Integrity**
    - **Validates: Requirements 4.2, 4.3, 6.2, 6.3, 7.2, 7.3, 9.2, 9.3**

  - [x] 3.5 Implement write operations (coils, holding registers)
    - Add methods for writing coils and holding registers
    - Implement value validation and error handling
    - _Requirements: 5.1, 5.2, 8.1, 8.2_

  - [x] 3.6 Write property test for write operations
    - **Property 7: Write Operation Validation**
    - **Validates: Requirements 5.4, 8.4**

- [x] 4. Implement connection manager
  - [x] 4.1 Create ConnectionManager class
    - Implement client creation, storage, and retrieval methods
    - Add unique ID generation for client connections
    - Implement client cleanup and resource management
    - Add serial port tracking for RTU clients
    - _Requirements: 1.3, 2.3, 3.4, 10.1, 10.5_

  - [x] 4.2 Implement serial port discovery
    - Add method to list available serial ports using pyserial
    - Track which ports are in use by active RTU clients
    - Return port availability status and descriptions
    - _Requirements: 11.1, 11.2, 11.3, 11.4_

  - [x] 4.3 Write property test for serial port discovery
    - **Property 10: Serial Port Discovery and Availability**
    - **Validates: Requirements 11.1, 11.2, 11.3**

  - [x] 4.4 Write property test for client uniqueness
    - **Property 1: Client Creation Uniqueness**
    - **Validates: Requirements 1.3, 2.3, 10.5**

  - [x] 4.5 Add concurrent client support
    - Implement thread-safe operations for multiple clients
    - Add client listing and status tracking functionality
    - _Requirements: 10.1, 10.2_

  - [x] 4.6 Write property test for concurrent clients
    - **Property 9: Concurrent Client Support**
    - **Validates: Requirements 10.1, 10.2**

- [ ] 5. Checkpoint - Core functionality complete
  - Ensure all tests pass, ask the user if questions arise.

- [x] 6. Implement MCP command handlers
  - [x] 6.1 Create ModbusCommandHandlers class
    - Implement handlers for all MCP tools (create clients, read/write operations)
    - Add parameter validation and error response formatting
    - _Requirements: 1.1, 2.1, 4.1, 5.1, 6.1, 7.1, 8.1, 9.1_

  - [x] 6.2 Write property test for valid parameter acceptance
    - **Property 2: Valid Parameter Acceptance**
    - **Validates: Requirements 1.1, 2.1**

  - [x] 6.3 Implement error handling for invalid client IDs
    - Add proper error responses for operations on non-existent clients
    - _Requirements: 3.2_

  - [x] 6.4 Write property test for invalid client ID handling
    - **Property 5: Invalid Client ID Handling**
    - **Validates: Requirements 3.2**

- [x] 7. Implement fastMCP server integration
  - [x] 7.1 Create main FastMCP server application
    - Set up fastMCP app with all required tools
    - Integrate ConnectionManager and CommandHandlers
    - Configure tool definitions and parameter schemas
    - _Requirements: All requirements - this is the main integration point_

  - [x] 7.2 Implement MCP tool functions
    - Create @app.tool() decorated functions for all Modbus operations
    - Add list_serial_ports tool for RTU port discovery
    - Wire tool functions to command handlers
    - Add proper parameter validation and response formatting
    - _Requirements: 1.1, 2.1, 3.1, 4.1, 5.1, 6.1, 7.1, 8.1, 9.1, 11.1_

  - [x] 7.3 Write property test for error message consistency
    - **Property 11: Error Message Consistency**
    - **Validates: Requirements 12.1, 12.2, 12.3, 12.5**

- [x] 8. Add comprehensive error handling
  - [x] 8.1 Implement pymodbus exception handling
    - Add try-catch blocks for all pymodbus operations
    - Convert pymodbus exceptions to user-friendly error messages
    - _Requirements: 12.5_

  - [x] 8.2 Add timeout and communication error handling
    - Implement timeout detection and reporting
    - Add retry logic for transient communication errors
    - _Requirements: 12.2, 12.3_

  - [x] 8.3 Write unit tests for error scenarios
    - Test specific error conditions and edge cases
    - Test timeout handling and communication failures
    - _Requirements: 12.2, 12.3, 12.5_

- [x] 9. Add configuration and CLI support
  - [x] 9.1 Create configuration management
    - Add support for configuration files and environment variables
    - Implement default values and validation
    - _Requirements: Supporting infrastructure for all requirements_

  - [x] 9.2 Add CLI entry point
    - Create command-line interface for starting the server
    - Add logging configuration and server options
    - _Requirements: Supporting infrastructure for all requirements_

- [x] 9.3 Write integration tests
  - Test end-to-end MCP server functionality
  - Test with mock Modbus devices and real MCP clients
  - _Requirements: All requirements - integration testing_

- [ ] 10. Final checkpoint and documentation
  - [x] 10.1 Ensure all tests pass and functionality works
    - Run complete test suite and verify all properties
    - Test with real MCP clients if possible
    - _Requirements: All requirements verification_

  - [x] 10.2 Create usage documentation and examples
    - Write README with installation and usage instructions
    - Create example MCP client configurations
    - _Requirements: Supporting documentation_

## Notes

- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation of functionality
- Property tests validate universal correctness properties from the design
- Unit tests validate specific examples and edge cases
- Integration tests ensure end-to-end functionality
- The implementation uses fastMCP 2.0 and pymodbus as specified in the design
- Serial port discovery enhances user experience by showing available ports and preventing conflicts