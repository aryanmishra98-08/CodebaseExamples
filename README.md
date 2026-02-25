# CodebaseExamples

# Warehouse Management Tool

A robust, command-line based location and inventory management system designed for warehouse operations with support for concurrent access and persistent state storage.

---

## Table of Contents

1. [Overview](#overview)
2. [Assignment](#assignment)
3. [About the Project](#about-the-project)
4. [Architecture](#architecture)
5. [Design Approach](#design-approach)
6. [Project Structure](#project-structure)
7. [Data Structures & Dependencies](#data-structures--dependencies)
8. [Installation](#installation)
9. [How to Use the System](#how-to-use-the-system)
10. [Testing](#testing)
11. [Error Handling](#error-handling)
12. [Future Enhancements](#future-enhancements)
13. [Troubleshooting](#troubleshooting)
14. [Acknowledgments](#acknowledgments)

---

## Overview

This warehouse management tool provides a complete solution for tracking inventory across multiple warehouse locations. The system operates as a command-line interface that reads commands from standard input (stdin) and writes responses to standard output (stdout), making it suitable for both interactive use and automation.

**Key Features:**
- Register and deregister warehouse locations
- Increment and decrement inventory quantities
- Transfer inventory between locations
- Observe current inventory at any location
- Persistent state storage with automatic save/load
- Concurrent access support for multiple processes
- Comprehensive error handling and validation
- Atomic operations to prevent data corruption

---

## Assignment

### Code Assignment — Rapyuta Robotics (Backend Software Engineer)

#### Overview

This tool was built as a take-home assignment to assess the ability to design and implement a simple, robust backend system. The target completion time is 2–4 hours, with one week allowed for submission.

**Constraints:**
- Python as the primary language
- Clean, organized, well-written code
- External dependencies are permitted
- No authentication required

---

#### Requirements

**Core Entities:**

- **Location** — A place in the warehouse where inventory may be stored, identified by a globally unique alphanumeric name (e.g., `LA` for Location A).
- **Inventory** — A pair of an item identifier (alphanumeric string, e.g., `IA`) and a positive quantity (integer > 0).

**Supported Operations:**

1. **Register / Deregister Locations**
   - Register a new location by unique name. Fails if already exists.
   - Deregister only if the location exists **and** has no inventory. Fails otherwise.

2. **Increment Inventory** — Add a specified quantity of an item to a location. Creates the item if it doesn't exist. Fails if the location doesn't exist.

3. **Decrement Inventory** — Subtract a specified quantity from an item in a location. Fails if the location doesn't exist, the item doesn't exist, or the resulting quantity would go below 0.

4. **Transfer Inventory** — Move a specified quantity of an item from one location to another. Fails if either location doesn't exist or the source has insufficient quantity.

5. **Observe Inventory** — Retrieve all items and quantities at a location, sorted alphabetically by item ID. Returns `EMPTY` if no items exist. Fails if the location doesn't exist.

---

#### Input / Output Specification

- **Interface:** Command-line tool reading from `stdin`, writing to `stdout`.
- **Format:** One command per line; responses written immediately after each command.

#### State Persistence

- Warehouse state must always be stored in a file (JSON, CSV, SQLite, etc. — format is your choice).
- State is loaded on startup (if the file exists) and saved after every successful write operation.
- **Concurrent access must be supported** — multiple instances of the tool may run simultaneously against the same state file.
- The persistence file path should be hardcoded (e.g., `warehouse_state.json`) or configurable via a CLI argument.

---

#### Command Reference

| Command | Syntax | Notes |
|---|---|---|
| Register Location | `LOCATION REGISTER <LOCATION_ID>` | Fails if already exists |
| Unregister Location | `LOCATION UNREGISTER <LOCATION_ID>` | Fails if not found or has inventory |
| Increment Inventory | `INVENTORY INCREMENT <LOCATION_ID> <ITEM_ID> <QUANTITY>` | Creates item if not present |
| Decrement Inventory | `INVENTORY DECREMENT <LOCATION_ID> <ITEM_ID> <QUANTITY>` | Fails if insufficient quantity |
| Transfer Inventory | `INVENTORY TRANSFER <SRC> <DEST> <ITEM_ID> <QUANTITY>` | Atomic move between locations |
| Observe Inventory | `INVENTORY OBSERVE <LOCATION_ID>` | Alphabetically sorted; `EMPTY` if none |

---

#### Example Input / Output

```
LOCATION REGISTER LA
> OK
LOCATION REGISTER LB
> OK
LOCATION REGISTER LA
> ERR: Location 'LA' already exists
INVENTORY INCREMENT LA IA 5
> OK
INVENTORY DECREMENT LA IA 3
> OK
INVENTORY DECREMENT LA IA 3
> ERR: Insufficient quantity of item IA in location LA (has 2)
INVENTORY TRANSFER LA LB IA 2
> OK
LOCATION UNREGISTER LA
> OK
LOCATION UNREGISTER LC
> ERR: Location 'LC' does not exist
LOCATION UNREGISTER LB
> ERR: Location 'LB' has inventories
INVENTORY OBSERVE LB
> ITEM IA 2
INVENTORY OBSERVE LA
> ERR: Location 'LA' does not exist
LOCATION REGISTER LA
> OK
INVENTORY OBSERVE LA
> EMPTY
```

---

#### Deliverables

A ZIP file containing:
- Source code and all files needed to run it (e.g., `pyproject.toml`, `Dockerfile`)
- A `README.md` covering:
  - Design decisions (data structures, persistence format, dependencies and rationale)
  - Instructions on how to run the code

---

## About the Project

This project was developed as a backend software engineering assignment to demonstrate the ability to design and implement a robust, file-based state management system with support for concurrent operations.

**Design Goals:**
1. **Simplicity**: Clean, maintainable code with clear separation of concerns
2. **Reliability**: Atomic operations with proper error handling
3. **Concurrency**: Support multiple processes accessing the same state file
4. **Persistence**: State survives application restarts
5. **Testability**: Comprehensive unit tests covering all operations

The implementation focuses on core backend principles: data consistency, error handling, file I/O, concurrency control, and system design.

---

## Architecture

### System Design and Interaction Overview

The system follows a layered architecture pattern with clear separation between the command-line interface and business logic:

```
┌─────────────────────────────────────────────────────┐
│                   User / Process                     │
└───────────────────┬─────────────────────────────────┘
                    │ stdin/stdout
                    ▼
┌─────────────────────────────────────────────────────┐
│              main.py (CLI Layer)                     │
│  - Command parsing                                   │
│  - Input/output formatting                           │
│  - User interaction                                  │
└───────────────────┬─────────────────────────────────┘
                    │ Function calls
                    ▼
┌─────────────────────────────────────────────────────┐
│      modules/Warehouse.py (Business Logic)           │
│  - Location management                               │
│  - Inventory operations                              │
│  - State validation                                  │
│  - Error handling                                    │
└───────────────────┬─────────────────────────────────┘
                    │ Read/Write with locking
                    ▼
┌─────────────────────────────────────────────────────┐
│      data/warehouse_state.json (Persistence)         │
│  - JSON format state file                            │
│  - Atomic writes via temp files                      │
│  - File locking for concurrent access                │
└─────────────────────────────────────────────────────┘
```

**Component Responsibilities:**

| Component | File | Responsibility |
|-----------|------|----------------|
| **CLI Interface** | `main.py` | Handles command parsing, input validation, and output formatting. Reads from stdin, writes to stdout. |
| **Business Logic** | `modules/Warehouse.py` | Implements core warehouse operations, state management, and business rules validation. |
| **Configuration** | `setup_loader.py` | Loads application configuration from YAML, sets up logging, ensures required directories exist. |
| **State Storage** | `data/warehouse_state.json` | Persistent JSON file storing all locations and their inventories. Auto-created on first run. |
| **Configuration File** | `config/app_config.yaml` | Contains logging settings and state file path configuration. |
| **Tests** | `test/test_warehouse.py` | Comprehensive unit tests for both business logic and CLI interface. |

**Data Flow:**
1. User enters a command via stdin
2. CLI parses the command and validates format
3. CLI calls appropriate Warehouse method
4. Warehouse loads current state from file (with file lock)
5. Warehouse validates operation and updates in-memory state
6. Warehouse saves updated state to file atomically (with file lock)
7. Warehouse returns success/error response
8. CLI formats and outputs response to stdout

---

## Design Approach

### Key Decisions and Reasoning

#### 1. **File-Based Persistence with JSON**
**Decision:** Use a JSON file for state storage instead of a database.

**Reasoning:**
- Simple to implement and debug
- Human-readable format
- No external database dependencies
- Sufficient for small to medium-scale operations
- Easy to backup and version control
- Portable across platforms

**Trade-off:** Not suitable for very high-volume operations or complex queries, but meets assignment requirements perfectly.

#### 2. **File Locking for Concurrency**
**Decision:** Implement file locking using `portalocker` library with exclusive locks.

**Reasoning:**
- Prevents race conditions when multiple processes access the same file
- Cross-platform compatibility (works on Windows, Linux, macOS)
- Timeout mechanism prevents deadlocks
- Standard solution for file-based concurrency control

**Implementation Details:**
- Exclusive lock (LOCK_EX) acquired before reading/writing
- 10-second timeout to prevent indefinite blocking
- Non-blocking lock attempts with retry logic
- Automatic lock release via context managers

#### 3. **Atomic File Writes**
**Decision:** Use temporary file + rename pattern for state saves.

**Reasoning:**
- Prevents data corruption if process crashes during write
- Ensures either old complete state or new complete state exists
- Never leaves a partially written/corrupted state file
- Standard pattern for atomic file operations

**Implementation:**
```python
# Write to temp file → Flush to disk → Rename (atomic operation)
temp_file = state_file.with_suffix('.tmp')
write_to(temp_file)
os.replace(temp_file, state_file)  # Atomic on all platforms
```

#### 4. **Layered Architecture**
**Decision:** Separate CLI logic from business logic.

**Reasoning:**
- Single Responsibility Principle - each module has one job
- Easier to test business logic independently
- Could easily add different interfaces (web API, GUI) later
- Cleaner code organization and maintainability

#### 5. **State Reload Before Each Operation**
**Decision:** Reload state from file before each operation.

**Reasoning:**
- Ensures we always work with the latest state
- Critical for concurrent access - other processes may have modified state
- Prevents stale data issues
- Slight performance cost is acceptable for correctness

#### 6. **Automatic Item Cleanup**
**Decision:** Remove items from location when quantity reaches zero.

**Reasoning:**
- Keeps state file clean and compact
- Makes "EMPTY" location detection simple
- Matches real-world warehouse behavior
- Reduces storage overhead

#### 7. **Comprehensive Error Messages**
**Decision:** Provide detailed, specific error messages with context.

**Reasoning:**
- Helps users understand what went wrong
- Includes relevant information (location names, quantities)
- Easier debugging and troubleshooting
- Better user experience

**Example:**
```
ERR: Insufficient quantity of item 'IA' in location 'LA' (has 2)
```
Instead of just:
```
ERR: Insufficient quantity
```

#### 8. **Configuration via YAML**
**Decision:** Use YAML for configuration with environment variable support.

**Reasoning:**
- More readable than JSON for configuration
- Supports comments
- Custom parser allows environment variable injection
- Centralized configuration management
- Easy to modify without code changes

#### 9. **Logging Infrastructure**
**Decision:** Implement comprehensive logging to rotating log files.

**Reasoning:**
- Debugging production issues
- Audit trail of operations
- Performance monitoring
- Separate from stdout (which is for command responses)
- Rotating files prevent disk space issues

---

## Project Structure

### Directory and Module Layout

```
Warehouse-Tool/
├── main.py                     # Application entry point and CLI interface
├── setup_loader.py             # Configuration loader and logging setup
├── requirements.txt            # Python package dependencies
│
├── modules/                    # Business logic modules
│   └── Warehouse.py           # Core warehouse operations and state management
│
├── config/                     # Configuration files
│   └── app_config.yaml        # Application settings (logging, state file path)
│
├── data/                       # Data storage directory
│   └── warehouse_state.json   # Persistent state file (auto-created)
│
├── logs/                       # Log files directory
│   └── main_system_logs.log   # Application logs (auto-created, rotates daily)
│
├── test/                       # Test suite
│   ├── __init__.py            # Python package marker
│   └── test_warehouse.py      # Unit tests for Warehouse and CLI
│
├── keys/                       # Environment variables
│   └── .env                   # Environment configuration file
│
├── run_tests.sh               # Linux/macOS test runner script
├── run_tests.cmd              # Windows test runner script
├── start_service.sh           # Linux/macOS application launcher
├── start_service.cmd          # Windows application launcher
│
└── README.md                  # This file
```

**Module Descriptions:**

**`main.py`** (192 lines)
- `WarehouseCLI` class: Main CLI interface
- Command parsing and validation
- Output formatting
- stdin/stdout handling
- Entry point (`main()` function)

**`modules/Warehouse.py`** (545 lines)
- `Warehouse` class: Core business logic
- Location operations: `register_location()`, `unregister_location()`
- Inventory operations: `increment_inventory()`, `decrement_inventory()`, `transfer_inventory()`, `observe_inventory()`
- State persistence: `_load_state()`, `_save_state()`
- File locking: `_acquire_lock()`, `_release_lock()`

**`setup_loader.py`** (95 lines)
- Configuration loading from YAML
- Custom YAML parser for environment variables
- Logging setup
- Directory initialization

**`test/test_warehouse.py`** (453 lines)
- 47 comprehensive unit tests
- Tests for all warehouse operations
- Tests for CLI command parsing and execution
- State persistence tests
- Error handling tests
- Integration workflow tests

---

## Data Structures & Dependencies

### Data Structures Chosen

#### 1. **In-Memory State: Nested Dictionary**
```python
state = {
    "LOCATION_ID": {
        "ITEM_ID": quantity,
        "ITEM_ID": quantity,
        ...
    },
    "LOCATION_ID": {
        ...
    }
}
```

**Reasoning:**
- O(1) lookup for location and item access
- Natural mapping of location → items → quantities
- Easy to serialize to JSON
- Memory efficient for small to medium datasets
- Simple to iterate and query

**Example:**
```python
{
    "LA": {
        "IA": 10,
        "IB": 5
    },
    "LB": {
        "IA": 3
    }
}
```

#### 2. **Response Format: Structured Dictionary**
```python
response = {
    'status': bool,        # True for success, False for error
    'message': str,        # Human-readable message
    'output': dict/str,    # Operation result (for OBSERVE)
    'error': str          # Error details (if status is False)
}
```

**Reasoning:**
- Consistent interface for all operations
- Easy to check success/failure
- Separates user messages from error details
- Extensible for future fields

### Import/Export Formats and Handling

#### JSON State File Format

**Structure:**
```json
{
  "LOCATION_ID_1": {
    "ITEM_ID_A": 10,
    "ITEM_ID_B": 5
  },
  "LOCATION_ID_2": {
    "ITEM_ID_A": 3
  }
}
```

**Characteristics:**
- Top-level keys: Location IDs (strings)
- Second-level keys: Item IDs (strings)
- Values: Quantities (positive integers)
- Empty locations: Empty dictionaries `{}`
- Items with zero quantity: Removed from state

**Write Process:**
1. Serialize in-memory state to JSON with indentation
2. Write to temporary file (`warehouse_state.json.tmp`)
3. Flush buffer and sync to disk (`fsync`)
4. Atomically rename temp file to actual file (`os.replace`)

**Read Process:**
1. Check if state file exists
2. Open file with shared read lock
3. Parse JSON into Python dictionary
4. Validate structure (ensure nested dict format)
5. Type conversion (ensure strings for IDs, ints for quantities)
6. Release lock

**Error Handling:**
- Missing file: Start with empty state `{}`
- Corrupted JSON: Log error, start with empty state
- Permission errors: Log error, fail gracefully

### External Dependencies Used and Why

**Listed in `requirements.txt`:**

#### 1. **`portalocker>=3.2.0`**
**Purpose:** Cross-platform file locking for concurrent access control

**Why chosen:**
- Pure Python implementation
- Works across Windows, Linux, and macOS
- Simple API with context manager support
- Well-maintained and widely used
- Handles edge cases (network drives, different filesystems)

**Usage in project:**
```python
portalocker.lock(file_handle, portalocker.LOCK_EX)  # Exclusive lock
portalocker.unlock(file_handle)                      # Release lock
```

**Alternative considered:** `fcntl` (Linux/Mac only, not portable)

#### 2. **`PyYAML>=6.0`**
**Purpose:** Parse and load YAML configuration files

**Why chosen:**
- Standard library for YAML in Python
- Supports custom tags and parsers
- Safe loading mode to prevent code injection
- Mature and stable

**Usage in project:**
- Load `config/app_config.yaml`
- Parse logging configuration
- Custom `!Parse` tag for environment variable injection

**Alternative considered:** JSON config files (less readable, no comments)

#### 3. **`python-dotenv>=1.0.0`**
**Purpose:** Load environment variables from `.env` files

**Why chosen:**
- Standard for environment variable management
- Keeps secrets out of code
- Easy configuration across environments (dev/test/prod)
- 12-factor app methodology compliance

**Usage in project:**
```python
load_dotenv("keys/.env")  # Load environment variables
os.environ.get('WAREHOUSE_STATE_FILE')  # Access in config
```

**Alternative considered:** System environment variables (less portable)

#### 4. **Standard Library Modules:**
- `json`: JSON serialization/deserialization
- `os`, `pathlib`: File and path operations
- `logging`: Application logging
- `sys`: stdin/stdout handling
- `time`: Timeout implementation for locks
- `unittest`: Testing framework
- `tempfile`, `shutil`: Test file management

**Dependency Philosophy:**
- Minimal external dependencies (only 3 third-party packages)
- All dependencies are mature and well-maintained
- Each dependency solves a specific, non-trivial problem
- No dependencies for "convenience" - only when necessary

---

## Installation

### Prerequisites

Before installing, ensure you have the following:

**Required:**
- **Python 3.9 or later** (tested with Python 3.11)
- **pip** (Python package installer)

**Supported Operating Systems:**
- Linux (Ubuntu, Debian, CentOS, etc.)
- macOS (10.14+)
- Windows (10, 11)

**Optional:**
- Git (to clone the repository)

### Setup Steps

#### Step 1: Download the Project

**Option A: Extract from ZIP**
```bash
unzip Warehouse-Tool.zip
cd Warehouse-Tool
```

#### Step 2: Install Python Dependencies

Install required packages using pip:

```bash
pip install -r requirements.txt
```

**Expected output:**
```
Successfully installed portalocker-3.2.0 PyYAML-6.0 python-dotenv-1.0.0
```

**For virtual environment (recommended):**
```bash
# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt
```

#### Step 3: Verify Directory Structure

The following directories should exist (they're included in the repository):

```bash
ls -la
```

Expected directories:
- `config/` - Configuration files
- `data/` - State file storage (warehouse_state.json will be auto-created)
- `logs/` - Log files (auto-created)
- `modules/` - Business logic
- `test/` - Unit tests

**Note:** If any directories are missing, they will be created automatically when you run the application.

#### Step 4: Configure Environment Variables (Optional)

If you want to use a custom state file location:

**Create environment file:**
```bash
mkdir -p keys
nano keys/.env
```

**Add configuration:**
```
WAREHOUSE_STATE_FILE=data/warehouse_state.json
```

**Note:** If this file doesn't exist, the default path `data/warehouse_state.json` will be used.

#### Step 5: Verify Installation

Run the test suite to ensure everything is working:

**Linux/macOS:**
```bash
./run_tests.sh
```

**Windows:**
```cmd
run_tests.cmd
```

**Or manually:**
```bash
python3 -m unittest discover -s test -p "test_warehouse.py" -v
```

**Expected output:**
```
Ran 47 tests in 0.020s

OK
```

✅ **Installation complete!** You're ready to use the system.

---

## How to Use the System

### Starting the Application

The warehouse tool reads commands from standard input (stdin) and writes results to standard output (stdout).

#### Interactive Mode (Recommended for testing)

**Linux/macOS:**
```bash
python3 main.py
```

**Windows:**
```cmd
python main.py
```

**Or using the launcher script:**
```bash
./start_service.sh  # Linux/macOS
start_service.cmd   # Windows
```

Now you can type commands directly:
```
LOCATION REGISTER LA
OK
INVENTORY INCREMENT LA IA 10
OK
INVENTORY OBSERVE LA
ITEM IA 10
```

Press `Ctrl+C` to exit.

#### Batch Mode (For automation)

Process commands from a file:

```bash
python3 main.py < commands.txt
```

Or pipe commands:

```bash
echo "LOCATION REGISTER LA" | python3 main.py
```

### Command Reference

All commands follow the format: `COMMAND SUBCOMMAND [ARGUMENTS]`

Commands are case-sensitive and should be entered in UPPERCASE.

---

#### 1. LOCATION REGISTER

**Register a new warehouse location.**

**Syntax:**
```
LOCATION REGISTER <LOCATION_ID>
```

**Parameters:**
- `LOCATION_ID`: Alphanumeric identifier for the location (e.g., LA, ZONE1, WH_A)

**Success Response:**
```
OK
```

**Error Responses:**
```
ERR: Location 'LA' already exists
```

**Example:**
```
LOCATION REGISTER LA
OK

LOCATION REGISTER WAREHOUSE_1
OK

LOCATION REGISTER LA
ERR: Location 'LA' already exists
```

---

#### 2. LOCATION UNREGISTER

**Remove an existing location (only if empty).**

**Syntax:**
```
LOCATION UNREGISTER <LOCATION_ID>
```

**Parameters:**
- `LOCATION_ID`: ID of the location to remove

**Success Response:**
```
OK
```

**Error Responses:**
```
ERR: Location 'LC' does not exist
ERR: Location 'LB' has inventories
```

**Example:**
```
LOCATION REGISTER LA
OK

LOCATION UNREGISTER LA
OK

LOCATION UNREGISTER LA
ERR: Location 'LA' does not exist
```

**Important:** Cannot unregister a location that contains inventory. Decrement all items first.

---

#### 3. INVENTORY INCREMENT

**Add quantity to an item at a location.**

**Syntax:**
```
INVENTORY INCREMENT <LOCATION_ID> <ITEM_ID> <QUANTITY>
```

**Parameters:**
- `LOCATION_ID`: Target location
- `ITEM_ID`: Alphanumeric item identifier
- `QUANTITY`: Positive integer to add

**Success Response:**
```
OK
```

**Error Responses:**
```
ERR: Location 'LX' does not exist
ERR: Quantity must be a valid integer
ERR: Quantity must be positive
```

**Example:**
```
LOCATION REGISTER LA
OK

INVENTORY INCREMENT LA IA 10
OK

INVENTORY INCREMENT LA IA 5
OK

# Now LA has 15 units of IA
```

**Behavior:**
- If item doesn't exist at location, it's created with the given quantity
- If item exists, quantity is added to current amount

---

#### 4. INVENTORY DECREMENT

**Subtract quantity from an item at a location.**

**Syntax:**
```
INVENTORY DECREMENT <LOCATION_ID> <ITEM_ID> <QUANTITY>
```

**Parameters:**
- `LOCATION_ID`: Source location
- `ITEM_ID`: Item to decrement
- `QUANTITY`: Positive integer to subtract

**Success Response:**
```
OK
```

**Error Responses:**
```
ERR: Location 'LX' does not exist
ERR: Item 'IX' does not exist in location 'LA'
ERR: Insufficient quantity of item 'IA' in location 'LA' (has 5)
```

**Example:**
```
INVENTORY INCREMENT LA IA 10
OK

INVENTORY DECREMENT LA IA 3
OK

# Now LA has 7 units of IA

INVENTORY DECREMENT LA IA 10
ERR: Insufficient quantity of item 'IA' in location 'LA' (has 7)
```

**Behavior:**
- Fails if location doesn't exist
- Fails if item doesn't exist at location
- Fails if insufficient quantity
- If decrement results in zero, item is removed from location

---

#### 5. INVENTORY TRANSFER

**Move quantity from one location to another.**

**Syntax:**
```
INVENTORY TRANSFER <SRC_LOCATION> <DEST_LOCATION> <ITEM_ID> <QUANTITY>
```

**Parameters:**
- `SRC_LOCATION`: Source location ID
- `DEST_LOCATION`: Destination location ID
- `ITEM_ID`: Item to transfer
- `QUANTITY`: Positive integer amount to move

**Success Response:**
```
OK
```

**Error Responses:**
```
ERR: Location 'LX' does not exist
ERR: Item 'IA' does not exist in location 'LA'
ERR: Insufficient quantity of item 'IA' in location 'LA' (has 3)
```

**Example:**
```
LOCATION REGISTER LA
OK
LOCATION REGISTER LB
OK

INVENTORY INCREMENT LA IA 10
OK

INVENTORY TRANSFER LA LB IA 4
OK

# Now LA has 6 units, LB has 4 units of IA
```

**Behavior:**
- Atomic operation (both decrement and increment happen together)
- Fails if either location doesn't exist
- Fails if source has insufficient quantity
- If item exists at destination, quantities are added
- If transfer removes all quantity from source, item is deleted from source

---

#### 6. INVENTORY OBSERVE

**View all inventory at a location.**

**Syntax:**
```
INVENTORY OBSERVE <LOCATION_ID>
```

**Parameters:**
- `LOCATION_ID`: Location to inspect

**Success Response (with items):**
```
ITEM <ITEM_ID_1> <QUANTITY>
ITEM <ITEM_ID_2> <QUANTITY>
...
```
Items are sorted alphabetically by item ID.

**Success Response (empty location):**
```
EMPTY
```

**Error Response:**
```
ERR: Location 'LX' does not exist
```

**Example:**
```
LOCATION REGISTER LA
OK

INVENTORY OBSERVE LA
EMPTY

INVENTORY INCREMENT LA IA 10
OK
INVENTORY INCREMENT LA IB 5
OK
INVENTORY INCREMENT LA IC 3
OK

INVENTORY OBSERVE LA
ITEM IA 10
ITEM IB 5
ITEM IC 3
```

---

### Complete Workflow Example

This example demonstrates a typical warehouse operation workflow:

```bash
# Start the application
python3 main.py
```

**Commands:**
```
# 1. Set up warehouse locations
LOCATION REGISTER DOCK_A
OK

LOCATION REGISTER SHELF_1
OK

LOCATION REGISTER SHELF_2
OK

# 2. Receive inventory at dock
INVENTORY INCREMENT DOCK_A WIDGET_X 100
OK

INVENTORY INCREMENT DOCK_A GADGET_Y 50
OK

# 3. Check what arrived
INVENTORY OBSERVE DOCK_A
ITEM GADGET_Y 50
ITEM WIDGET_X 100

# 4. Move inventory to shelves
INVENTORY TRANSFER DOCK_A SHELF_1 WIDGET_X 60
OK

INVENTORY TRANSFER DOCK_A SHELF_2 WIDGET_X 40
OK

# 5. Check dock now
INVENTORY OBSERVE DOCK_A
ITEM GADGET_Y 50

# 6. Fulfill an order from shelf 1
INVENTORY DECREMENT SHELF_1 WIDGET_X 15
OK

INVENTORY OBSERVE SHELF_1
ITEM WIDGET_X 45

# 7. Try to remove dock (will fail - has inventory)
LOCATION UNREGISTER DOCK_A
ERR: Location 'DOCK_A' has inventories

# 8. Move remaining gadgets
INVENTORY TRANSFER DOCK_A SHELF_2 GADGET_Y 50
OK

# 9. Now dock is empty
INVENTORY OBSERVE DOCK_A
EMPTY

# 10. Remove dock successfully
LOCATION UNREGISTER DOCK_A
OK

# Press Ctrl+C to exit
```

### Using with Files

**Create a command file (`daily_operations.txt`):**
```
LOCATION REGISTER RECEIVING
INVENTORY INCREMENT RECEIVING PALLET_001 100
LOCATION REGISTER STORAGE_A
INVENTORY TRANSFER RECEIVING STORAGE_A PALLET_001 100
LOCATION UNREGISTER RECEIVING
```

**Execute:**
```bash
python3 main.py < daily_operations.txt
```

**Output:**
```
OK
OK
OK
OK
OK
```

### State Persistence

The warehouse state is automatically saved after every successful operation. You can:

1. **Stop and restart** the application - state is preserved
2. **Run multiple instances** - concurrent access is handled with file locking
3. **Manually inspect state** - view `data/warehouse_state.json`

---

## Testing

### Running Tests

The project includes comprehensive unit tests covering all functionality.

#### Run All Tests

**Using test scripts:**
```bash
./run_tests.sh       # Linux/macOS
run_tests.cmd        # Windows
```

**Using Python directly:**
```bash
python3 -m unittest discover -s test -p "test_warehouse.py" -v
```

#### Expected Output

```
test_decrement_inventory_insufficient_quantity ... ok
test_decrement_inventory_item_not_exists ... ok
test_decrement_inventory_success ... ok
...
test_transfer_inventory_success ... ok
test_unregister_location_success ... ok

----------------------------------------------------------------------
Ran 47 tests in 0.020s

OK
```

### Test Coverage

The test suite includes 47 tests across two test classes:

#### TestWarehouse (31 tests)
- Location registration (4 tests)
- Location unregistration (3 tests)
- Inventory increment (6 tests)
- Inventory decrement (5 tests)
- Inventory transfer (7 tests)
- Inventory observation (4 tests)
- State persistence (2 tests)

#### TestWarehouseCLI (16 tests)
- Command parsing (4 tests)
- Command execution (6 tests)
- Error handling (2 tests)
- Integration workflows (4 tests)

**Coverage includes:**
- ✅ Happy path scenarios
- ✅ Error conditions
- ✅ Edge cases (zero quantities, empty locations, etc.)
- ✅ Concurrent state modifications
- ✅ State persistence across restarts
- ✅ Invalid input handling
- ✅ Complete workflow integration

### Test Isolation

Each test:
- Uses a temporary state file
- Is independent of other tests
- Cleans up after itself
- Can run in any order

---

## Error Handling

### How Errors Are Detected, Handled, and Logged

The application implements comprehensive error handling at multiple levels:

#### 1. Input Validation

**Location/Type Checks:**
- Verify location exists before operations
- Check item exists before decrement/transfer
- Validate quantity is a positive integer

**Examples:**
```python
if location_id not in self.state:
    return error_response("Location '{}' does not exist".format(location_id))

if quantity <= 0:
    return error_response("Quantity must be positive")
```

#### 2. Business Rule Validation

**Constraint Enforcement:**
- Cannot unregister location with inventory
- Cannot decrement below zero
- Cannot transfer more than available

**Examples:**
```python
if self.state[location_id]:  # Has items
    return error_response("Location '{}' has inventories".format(location_id))

if current_qty < quantity:
    return error_response(
        "Insufficient quantity of item '{}' in location '{}' (has {})".format(
            item_id, location_id, current_qty
        )
    )
```

#### 3. File System Error Handling

**File Operations:**
- Missing state file: Create new empty state
- Corrupted JSON: Log error, start fresh
- Lock acquisition timeout: Log and fail gracefully
- Permission errors: Log and report

**Example:**
```python
try:
    if self.state_file.exists():
        with self.state_file.open('r') as f:
            data = json.load(f)
    else:
        self.state = {}
except Exception as e:
    logger.error("Failed to load warehouse state: %s", e)
    self.state = {}
```

#### 4. Concurrency Control

**File Locking:**
- Timeout mechanism prevents deadlock
- Retry logic with exponential backoff
- Graceful failure if lock cannot be acquired

**Example:**
```python
start_time = time.time()
while True:
    try:
        portalocker.lock(file_handle, portalocker.LOCK_EX | portalocker.LOCK_NB)
        return True
    except portalocker.exceptions.LockException:
        if time.time() - start_time >= timeout:
            logger.error("Failed to acquire lock within timeout")
            return False
        time.sleep(0.1)
```

### Error Response Format

All errors follow a consistent format:

**Structure:**
```
ERR: <detailed error message>
```

**Examples:**
```
ERR: Location 'LA' already exists
ERR: Location 'LC' does not exist
ERR: Location 'LB' has inventories
ERR: Item 'IA' does not exist in location 'LA'
ERR: Insufficient quantity of item 'IA' in location 'LA' (has 2)
ERR: Quantity must be a valid integer
ERR: Quantity must be positive
```

**Design Principles:**
- Specific and actionable
- Include relevant context (location names, current quantities)
- User-friendly language
- Consistent "ERR:" prefix for easy parsing

### Logging System

**Log Levels:**
- `INFO`: Normal operations (startup, shutdown, successful commands)
- `ERROR`: Operation failures, validation errors
- `WARNING`: Non-critical issues (lock release failures)
- `DEBUG`: Detailed execution traces (command processing)

**Log File:**
- Location: `logs/main_system_logs.log`
- Rotation: Daily at midnight
- Retention: 30 days
- Format: `TIMESTAMP - LEVEL - FILE:LINE - MESSAGE`

**Example log entries:**
```
2025-11-30 14:23:15 - INFO - main.py:153 - Warehouse CLI started
2025-11-30 14:23:20 - DEBUG - main.py:160 - Processing command: LOCATION REGISTER LA
2025-11-30 14:23:25 - ERROR - Warehouse.py:174 - Location 'LA' already exists
2025-11-30 14:24:10 - INFO - main.py:179 - Warehouse CLI stopped
```

**Configuration:**
See `config/app_config.yaml` for logging settings.

### Exception Handling Strategy

**Try-Except Blocks:**
- Wrap all file I/O operations
- Catch specific exceptions when possible
- Always log unexpected exceptions
- Provide user-friendly error messages
- Never expose internal stack traces to users (logged instead)

**Example:**
```python
try:
    quantity = int(quantity)
except ValueError:
    return error_response("Quantity must be a valid integer")
except Exception as e:
    logger.error("Unexpected error: %s", e)
    return error_response("Internal error occurred")
```

---

## Future Enhancements

While the current implementation meets all requirements, here are potential improvements for production use:

### Scalability Improvements

| Current Limitation | Proposed Enhancement | Benefit |
|--------------------|---------------------|---------|
| JSON file may not scale to millions of items | Migrate to SQLite or PostgreSQL | Better performance for large datasets |
| File locking has timeout limits | Implement queuing system | Handle high concurrency better |
| Single file limits distributed deployment | Add network-based locking (Redis) | Support distributed systems |

### Feature Additions

| Feature | Description | Use Case |
|---------|-------------|----------|
| **User Authentication** | Add login system with user roles | Multi-user warehouse operations |
| **Batch Operations** | Support multiple commands in one transaction | Atomic multi-step operations |
| **Item Metadata** | Track item names, descriptions, categories | Better inventory management |
| **Location Hierarchy** | Support nested locations (warehouse > aisle > shelf) | Complex warehouse layouts |
| **Audit Trail** | Track all changes with timestamps and user info | Compliance and debugging |
| **Search/Query** | Find items across all locations | Inventory location tracking |
| **Export/Import** | CSV/Excel import/export | Data migration and reporting |

### Interface Improvements

| Enhancement | Description | Benefit |
|-------------|-------------|---------|
| **Web UI** | Browser-based interface | Easier for non-technical users |
| **REST API** | HTTP API for integration | Third-party system integration |
| **TUI** | Terminal UI with menus | Better interactive experience |
| **GraphQL API** | Flexible query interface | Complex data retrieval |

### Operational Enhancements

| Feature | Description | Benefit |
|---------|-------------|---------|
| **Metrics Dashboard** | Real-time statistics and graphs | Operational visibility |
| **Alerts** | Notifications for low stock, errors | Proactive management |
| **Backup/Restore** | Automated state backups | Disaster recovery |
| **Health Checks** | System health monitoring | Reliability |

---

## Troubleshooting

### Common Issues and Solutions

#### Installation Issues

**Problem:** `ModuleNotFoundError: No module named 'portalocker'`

**Solution:**
```bash
pip install -r requirements.txt
```
Ensure you're in the project root directory.

---

**Problem:** `Permission denied` when creating directories

**Solution:**
```bash
# Ensure you have write permissions
chmod +x run_tests.sh start_service.sh
sudo chown -R $USER:$USER .
```

---

#### Runtime Issues

**Problem:** `ERR: Internal error - [Errno 13] Permission denied`

**Solution:**
Check that the `data/` directory is writable:
```bash
ls -la data/
chmod 755 data/
```

---

**Problem:** Commands not responding / hanging

**Cause:** Another process has locked the state file

**Solution:**
1. Wait 10 seconds for lock timeout
2. Check for other running instances
3. Remove stale lock (use cautiously):
```bash
rm -f data/warehouse_state.json.lock  # If exists
```

---

**Problem:** State file corrupted or unreadable

**Solution:**
The system will automatically create a new empty state. To recover:
1. Check `logs/main_system_logs.log` for error details
2. Manually inspect `data/warehouse_state.json`
3. Fix JSON syntax or restore from backup
4. Or delete and restart fresh:
```bash
rm data/warehouse_state.json
python3 main.py
```

---

#### Testing Issues

**Problem:** Tests failing with `ModuleNotFoundError`

**Solution:**
Run tests from project root directory:
```bash
cd /path/to/Warehouse-Tool
python3 -m unittest discover -s test -p "test_warehouse.py"
```

---

**Problem:** Tests fail intermittently

**Cause:** Concurrent test execution or leftover test files

**Solution:**
```bash
# Clean test artifacts
rm -rf /tmp/tmp*  # Linux/macOS
# Run tests sequentially
python3 -m unittest test.test_warehouse -v
```

---

#### Command Issues

**Problem:** `ERR: Invalid LOCATION command format`

**Cause:** Missing arguments

**Solution:**
Ensure proper syntax:
```
✗ LOCATION REGISTER
✓ LOCATION REGISTER LA
```

---

**Problem:** `ERR: Unknown command 'location'`

**Cause:** Commands are case-sensitive

**Solution:**
Use UPPERCASE:
```
✗ location register LA
✓ LOCATION REGISTER LA
```

---

### Getting Help

If you encounter issues not covered here:

1. **Check logs:** `cat logs/main_system_logs.log | tail -50`
2. **Run tests:** `./run_tests.sh` to verify installation
3. **Verify state:** `cat data/warehouse_state.json` to inspect state
4. **Check permissions:** Ensure read/write access to `data/` and `logs/`
5. **Review documentation:** Re-read relevant sections above

---

## Acknowledgments

### Thank You Note

This project was developed as part of a assessment for **Rapyuta Robotics**. I would like to express my gratitude for the opportunity to work on this interesting and challenging problem.

---

### Final Notes

This warehouse management tool demonstrates backend engineering principles including state management, concurrency control, error handling, and system design. While designed as an assignment solution, the architecture is production-ready and could be extended for real-world use cases.

The focus throughout development was on **correctness**, **reliability**, and **clarity** - ensuring the system does exactly what it should, handles errors gracefully, and is easy to understand and maintain.

Thank you for reviewing this project!

---
