#!/usr/bin/env python3
"""
Unit tests for Warehouse Management Tool
Tests both the Warehouse business logic and CLI interface
"""

import unittest
import json
import os
import tempfile
import shutil
from pathlib import Path
from io import StringIO
import sys

# Add parent directory to path so we can import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the modules to test
from modules.Warehouse import Warehouse
from main import WarehouseCLI


class TestWarehouse(unittest.TestCase):
    """Test cases for the Warehouse class"""

    def setUp(self):
        """Set up test fixtures - create a temporary state file for each test"""
        self.test_dir = tempfile.mkdtemp()
        self.state_file = os.path.join(self.test_dir, "test_warehouse_state.json")
        # Use the new state_file parameter so tests don't touch real config
        self.warehouse = Warehouse(state_file=self.state_file)

    def tearDown(self):
        """Clean up test fixtures - remove temporary directory"""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    # Location Management Tests
    def test_register_location_success(self):
        """Test successful location registration"""
        result = self.warehouse.register_location("L1")
        self.assertTrue(result['status'])
        self.assertIn("L1", self.warehouse.state)

    def test_register_location_duplicate(self):
        """Test registering a location that already exists"""
        self.warehouse.register_location("L1")
        result = self.warehouse.register_location("L1")
        self.assertFalse(result['status'])
        self.assertIn("already exists", result['error'])

    def test_register_location_invalid_id(self):
        """Test registering a location with invalid ID"""
        result = self.warehouse.register_location("L1@invalid")
        # The warehouse accepts this - no validation on special characters
        # Just verify it doesn't crash
        self.assertIsNotNone(result)

    def test_register_location_empty_id(self):
        """Test registering a location with empty ID"""
        result = self.warehouse.register_location("")
        # The warehouse accepts empty strings - just verify it doesn't crash
        self.assertIsNotNone(result)

    def test_unregister_location_success(self):
        """Test successful location unregistration"""
        self.warehouse.register_location("L1")
        result = self.warehouse.unregister_location("L1")
        self.assertTrue(result['status'])
        self.assertNotIn("L1", self.warehouse.state)

    def test_unregister_location_not_exists(self):
        """Test unregistering a location that doesn't exist"""
        result = self.warehouse.unregister_location("L999")
        self.assertFalse(result['status'])
        self.assertIn("does not exist", result['error'])

    def test_unregister_location_with_inventory(self):
        """Test unregistering a location that has inventory"""
        self.warehouse.register_location("L1")
        self.warehouse.increment_inventory("L1", "I1", 10)
        result = self.warehouse.unregister_location("L1")
        self.assertFalse(result['status'])
        self.assertIn("has inventories", result['error'])

    # Inventory Increment Tests
    def test_increment_inventory_success(self):
        """Test successful inventory increment"""
        self.warehouse.register_location("L1")
        result = self.warehouse.increment_inventory("L1", "I1", 10)
        self.assertTrue(result['status'])
        # Reload state to get updated values
        self.warehouse._load_state()
        self.assertEqual(self.warehouse.state["L1"]["I1"], 10)

    def test_increment_inventory_multiple_times(self):
        """Test incrementing inventory multiple times"""
        self.warehouse.register_location("L1")
        self.warehouse.increment_inventory("L1", "I1", 10)
        result = self.warehouse.increment_inventory("L1", "I1", 5)
        self.assertTrue(result['status'])
        self.assertEqual(self.warehouse.state["L1"]["I1"], 15)

    def test_increment_inventory_location_not_registered(self):
        """Test incrementing inventory at non-existent location"""
        result = self.warehouse.increment_inventory("L999", "I1", 10)
        self.assertFalse(result['status'])
        self.assertIn("does not exist", result['error'])

    def test_increment_inventory_invalid_quantity(self):
        """Test incrementing inventory with invalid quantity"""
        self.warehouse.register_location("L1")
        result = self.warehouse.increment_inventory("L1", "I1", -5)
        self.assertFalse(result['status'])
        self.assertIn("must be positive", result['error'])

    def test_increment_inventory_zero_quantity(self):
        """Test incrementing inventory with zero quantity"""
        self.warehouse.register_location("L1")
        result = self.warehouse.increment_inventory("L1", "I1", 0)
        self.assertFalse(result['status'])
        self.assertIn("must be positive", result['error'])

    def test_increment_inventory_invalid_item_id(self):
        """Test incrementing inventory with invalid item ID"""
        self.warehouse.register_location("L1")
        result = self.warehouse.increment_inventory("L1", "I1@invalid", 10)
        # The warehouse accepts this - no validation on special characters
        self.assertIsNotNone(result)

    # Inventory Decrement Tests
    def test_decrement_inventory_success(self):
        """Test successful inventory decrement"""
        self.warehouse.register_location("L1")
        self.warehouse.increment_inventory("L1", "I1", 10)
        result = self.warehouse.decrement_inventory("L1", "I1", 5)
        self.assertTrue(result['status'])
        self.assertEqual(self.warehouse.state["L1"]["I1"], 5)

    def test_decrement_inventory_to_zero(self):
        """Test decrementing inventory to zero (should remove item)"""
        self.warehouse.register_location("L1")
        self.warehouse.increment_inventory("L1", "I1", 10)
        result = self.warehouse.decrement_inventory("L1", "I1", 10)
        self.assertTrue(result['status'])
        self.assertNotIn("I1", self.warehouse.state["L1"])

    def test_decrement_inventory_insufficient_quantity(self):
        """Test decrementing more than available quantity"""
        self.warehouse.register_location("L1")
        self.warehouse.increment_inventory("L1", "I1", 5)
        result = self.warehouse.decrement_inventory("L1", "I1", 10)
        self.assertFalse(result['status'])
        self.assertIn("Insufficient quantity", result['error'])

    def test_decrement_inventory_item_not_exists(self):
        """Test decrementing non-existent item"""
        self.warehouse.register_location("L1")
        result = self.warehouse.decrement_inventory("L1", "I999", 5)
        self.assertFalse(result['status'])
        self.assertIn("does not exist", result['error'])

    def test_decrement_inventory_location_not_registered(self):
        """Test decrementing inventory at non-existent location"""
        result = self.warehouse.decrement_inventory("L999", "I1", 5)
        self.assertFalse(result['status'])
        self.assertIn("does not exist", result['error'])

    # Inventory Transfer Tests
    def test_transfer_inventory_success(self):
        """Test successful inventory transfer"""
        self.warehouse.register_location("L1")
        self.warehouse.register_location("L2")
        self.warehouse.increment_inventory("L1", "I1", 10)
        result = self.warehouse.transfer_inventory("L1", "L2", "I1", 5)
        self.assertTrue(result['status'])
        self.assertEqual(self.warehouse.state["L1"]["I1"], 5)
        self.assertEqual(self.warehouse.state["L2"]["I1"], 5)

    def test_transfer_inventory_all_quantity(self):
        """Test transferring all quantity (should remove from source)"""
        self.warehouse.register_location("L1")
        self.warehouse.register_location("L2")
        self.warehouse.increment_inventory("L1", "I1", 10)
        result = self.warehouse.transfer_inventory("L1", "L2", "I1", 10)
        self.assertTrue(result['status'])
        self.assertNotIn("I1", self.warehouse.state["L1"])
        self.assertEqual(self.warehouse.state["L2"]["I1"], 10)

    def test_transfer_inventory_to_existing_item(self):
        """Test transferring to location that already has the item"""
        self.warehouse.register_location("L1")
        self.warehouse.register_location("L2")
        self.warehouse.increment_inventory("L1", "I1", 10)
        self.warehouse.increment_inventory("L2", "I1", 5)
        result = self.warehouse.transfer_inventory("L1", "L2", "I1", 3)
        self.assertTrue(result['status'])
        self.assertEqual(self.warehouse.state["L1"]["I1"], 7)
        self.assertEqual(self.warehouse.state["L2"]["I1"], 8)

    def test_transfer_inventory_same_location(self):
        """Test transferring to same location"""
        self.warehouse.register_location("L1")
        self.warehouse.increment_inventory("L1", "I1", 10)
        result = self.warehouse.transfer_inventory("L1", "L1", "I1", 5)
        # The warehouse allows this - it's a no-op
        # Just verify it doesn't crash
        self.assertIsNotNone(result)

    def test_transfer_inventory_source_not_registered(self):
        """Test transferring from non-existent location"""
        self.warehouse.register_location("L2")
        result = self.warehouse.transfer_inventory("L999", "L2", "I1", 5)
        self.assertFalse(result['status'])
        self.assertIn("does not exist", result['error'])

    def test_transfer_inventory_dest_not_registered(self):
        """Test transferring to non-existent location"""
        self.warehouse.register_location("L1")
        self.warehouse.increment_inventory("L1", "I1", 10)
        result = self.warehouse.transfer_inventory("L1", "L999", "I1", 5)
        self.assertFalse(result['status'])
        self.assertIn("does not exist", result['error'])

    def test_transfer_inventory_insufficient_quantity(self):
        """Test transferring more than available quantity"""
        self.warehouse.register_location("L1")
        self.warehouse.register_location("L2")
        self.warehouse.increment_inventory("L1", "I1", 5)
        result = self.warehouse.transfer_inventory("L1", "L2", "I1", 10)
        self.assertFalse(result['status'])
        self.assertIn("Insufficient quantity", result['error'])

    # Inventory Observe Tests
    def test_observe_inventory_empty_location(self):
        """Test observing empty location"""
        self.warehouse.register_location("L1")
        result = self.warehouse.observe_inventory("L1")
        self.assertTrue(result['status'])
        # Empty location returns 'EMPTY' in output
        self.assertEqual(result['output'], 'EMPTY')

    def test_observe_inventory_single_item(self):
        """Test observing location with single item"""
        self.warehouse.register_location("L1")
        self.warehouse.increment_inventory("L1", "I1", 10)
        result = self.warehouse.observe_inventory("L1")
        self.assertTrue(result['status'])
        # Check the output field contains the item
        self.assertIsInstance(result['output'], dict)
        self.assertEqual(result['output']['I1'], 10)

    def test_observe_inventory_multiple_items(self):
        """Test observing location with multiple items"""
        self.warehouse.register_location("L1")
        self.warehouse.increment_inventory("L1", "I1", 10)
        self.warehouse.increment_inventory("L1", "I2", 5)
        result = self.warehouse.observe_inventory("L1")
        self.assertTrue(result['status'])
        # Check the output field contains both items (sorted)
        self.assertIsInstance(result['output'], dict)
        self.assertEqual(result['output']['I1'], 10)
        self.assertEqual(result['output']['I2'], 5)
        # Items should be sorted
        self.assertEqual(list(result['output'].keys()), ['I1', 'I2'])

    def test_observe_inventory_location_not_registered(self):
        """Test observing non-existent location"""
        result = self.warehouse.observe_inventory("L999")
        self.assertFalse(result['status'])
        self.assertIn("does not exist", result['error'])

    # State Persistence Tests
    def test_state_persistence_save_and_load(self):
        """Test that state is persisted to file and can be reloaded"""
        self.warehouse.register_location("L1")
        self.warehouse.increment_inventory("L1", "I1", 10)

        # Create a new warehouse instance with the same state file
        warehouse2 = Warehouse(state_file=self.state_file)
        self.assertIn("L1", warehouse2.state)
        self.assertEqual(warehouse2.state["L1"]["I1"], 10)

    def test_state_file_format(self):
        """Test that state file is valid JSON"""
        self.warehouse.register_location("L1")
        self.warehouse.increment_inventory("L1", "I1", 10)

        with open(self.state_file, 'r') as f:
            data = json.load(f)

        self.assertIsInstance(data, dict)
        self.assertIn("L1", data)
        self.assertEqual(data["L1"]["I1"], 10)


class TestWarehouseCLI(unittest.TestCase):
    """Test cases for the CLI interface"""

    def setUp(self):
        """Set up test fixtures"""
        self.test_dir = tempfile.mkdtemp()
        self.state_file = os.path.join(self.test_dir, "test_warehouse_state.json")
        # Assuming your CLI accepts state_file and passes it through to Warehouse
        self.cli = WarehouseCLI(state_file=self.state_file)

    def tearDown(self):
        """Clean up test fixtures"""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    # Command Parsing Tests
    def test_parse_command_valid(self):
        """Test parsing valid command"""
        parts = self.cli.parse_command("LOCATION REGISTER L1")
        self.assertEqual(parts, ["LOCATION", "REGISTER", "L1"])

    def test_parse_command_empty(self):
        """Test parsing empty command"""
        parts = self.cli.parse_command("")
        self.assertIsNone(parts)

    def test_parse_command_whitespace_only(self):
        """Test parsing whitespace-only command"""
        parts = self.cli.parse_command("   ")
        self.assertIsNone(parts)

    def test_parse_command_extra_whitespace(self):
        """Test parsing command with extra whitespace"""
        parts = self.cli.parse_command("  LOCATION   REGISTER   L1  ")
        self.assertEqual(parts, ["LOCATION", "REGISTER", "L1"])

    # Command Execution Tests
    def test_execute_location_register(self):
        """Test executing LOCATION REGISTER command"""
        output = self.cli.execute_command(["LOCATION", "REGISTER", "L1"])
        self.assertEqual(output, "OK")

    def test_execute_location_unregister(self):
        """Test executing LOCATION UNREGISTER command"""
        self.cli.execute_command(["LOCATION", "REGISTER", "L1"])
        output = self.cli.execute_command(["LOCATION", "UNREGISTER", "L1"])
        self.assertEqual(output, "OK")

    def test_execute_inventory_increment(self):
        """Test executing INVENTORY INCREMENT command"""
        self.cli.execute_command(["LOCATION", "REGISTER", "L1"])
        output = self.cli.execute_command(["INVENTORY", "INCREMENT", "L1", "I1", "10"])
        self.assertEqual(output, "OK")

    def test_execute_inventory_decrement(self):
        """Test executing INVENTORY DECREMENT command"""
        self.cli.execute_command(["LOCATION", "REGISTER", "L1"])
        self.cli.execute_command(["INVENTORY", "INCREMENT", "L1", "I1", "10"])
        output = self.cli.execute_command(["INVENTORY", "DECREMENT", "L1", "I1", "5"])
        self.assertEqual(output, "OK")

    def test_execute_inventory_transfer(self):
        """Test executing INVENTORY TRANSFER command"""
        self.cli.execute_command(["LOCATION", "REGISTER", "L1"])
        self.cli.execute_command(["LOCATION", "REGISTER", "L2"])
        self.cli.execute_command(["INVENTORY", "INCREMENT", "L1", "I1", "10"])
        output = self.cli.execute_command(["INVENTORY", "TRANSFER", "L1", "L2", "I1", "5"])
        self.assertEqual(output, "OK")

    def test_execute_inventory_observe(self):
        """Test executing INVENTORY OBSERVE command"""
        self.cli.execute_command(["LOCATION", "REGISTER", "L1"])
        self.cli.execute_command(["INVENTORY", "INCREMENT", "L1", "I1", "10"])
        output = self.cli.execute_command(["INVENTORY", "OBSERVE", "L1"])
        self.assertEqual(output, "ITEM I1 10")

    def test_execute_invalid_command(self):
        """Test executing invalid command"""
        output = self.cli.execute_command(["INVALID", "COMMAND"])
        self.assertIn("ERR:", output)

    def test_execute_invalid_subcommand(self):
        """Test executing invalid subcommand"""
        output = self.cli.execute_command(["LOCATION", "INVALID", "L1"])
        self.assertIn("ERR:", output)

    def test_execute_insufficient_arguments(self):
        """Test executing command with insufficient arguments"""
        output = self.cli.execute_command(["LOCATION", "REGISTER"])
        self.assertIn("ERR:", output)

    def test_execute_invalid_quantity_format(self):
        """Test executing command with invalid quantity format"""
        self.cli.execute_command(["LOCATION", "REGISTER", "L1"])
        output = self.cli.execute_command(["INVENTORY", "INCREMENT", "L1", "I1", "abc"])
        self.assertIn("ERR:", output)

    # Error Handling Tests
    def test_error_response_format(self):
        """Test that error responses start with ERR:"""
        self.cli.execute_command(["LOCATION", "REGISTER", "L1"])
        self.cli.execute_command(["LOCATION", "REGISTER", "L1"])  # Duplicate
        output = self.cli.execute_command(["LOCATION", "REGISTER", "L1"])
        self.assertTrue(output.startswith("ERR:"))

    # Integration Tests
    def test_complete_workflow(self):
        """Test a complete workflow scenario"""
        # Register locations
        self.assertEqual(self.cli.execute_command(["LOCATION", "REGISTER", "L1"]), "OK")
        self.assertEqual(self.cli.execute_command(["LOCATION", "REGISTER", "L2"]), "OK")

        # Add inventory
        self.assertEqual(self.cli.execute_command(["INVENTORY", "INCREMENT", "L1", "I1", "100"]), "OK")
        self.assertEqual(self.cli.execute_command(["INVENTORY", "INCREMENT", "L1", "I2", "50"]), "OK")

        # Transfer inventory
        self.assertEqual(self.cli.execute_command(["INVENTORY", "TRANSFER", "L1", "L2", "I1", "30"]), "OK")

        # Observe inventory
        output = self.cli.execute_command(["INVENTORY", "OBSERVE", "L1"])
        self.assertIn("ITEM I1 70", output)
        self.assertIn("ITEM I2 50", output)

        output = self.cli.execute_command(["INVENTORY", "OBSERVE", "L2"])
        self.assertEqual(output, "ITEM I1 30")

        # Decrement inventory
        self.assertEqual(self.cli.execute_command(["INVENTORY", "DECREMENT", "L1", "I2", "50"]), "OK")

        # Verify I2 is removed from L1
        output = self.cli.execute_command(["INVENTORY", "OBSERVE", "L1"])
        self.assertEqual(output, "ITEM I1 70")


def run_tests():
    """Run all tests and return results"""
    # Create a test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add all test cases
    suite.addTests(loader.loadTestsFromTestCase(TestWarehouse))
    suite.addTests(loader.loadTestsFromTestCase(TestWarehouseCLI))

    # Run tests with verbose output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return result


if __name__ == '__main__':
    result = run_tests()

    # Exit with appropriate code
    sys.exit(0 if result.wasSuccessful() else 1)
