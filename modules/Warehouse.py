from setup_loader import config_data, logger
import json
import os
import portalocker
import time
from pathlib import Path


class Warehouse:
    """
    Warehouse manager for locations and inventory stored in a JSON file.
    """

    def __init__(self, state_file=None):
        """
        Initialize the Warehouse with the JSON state file.

        Args:
            state_file (str, optional): Path to the JSON state file. If not provided,
                                        it will try to read from config_data['warehouse']['state_file'].
        """
        if state_file is None:
            state_file = config_data["warehouse"]["state_file"]
        self.state_file = Path(state_file)

        self.state = {}
        self._load_state()

    # -----------------------
    # Internal helpers
    # -----------------------

    def _success_response(self, message, output=''):
        return {
            'status': True,
            'message': message,
            'output': output,
            'error': ''
        }

    def _error_response(self, message, error):
        return {
            'status': False,
            'message': message,
            'output': '',
            'error': error
        }

    def _acquire_lock(self, file_handle, timeout=10):
        """
        Acquire an exclusive lock on the file with timeout using portalocker.

        Args:
            file_handle: Open file handle to lock
            timeout (int): Maximum seconds to wait for lock

        Returns:
            bool: True if lock acquired, False otherwise
        """
        start_time = time.time()
        while True:
            try:
                # Non-blocking lock attempt
                portalocker.lock(
                    file_handle,
                    portalocker.LOCK_EX | portalocker.LOCK_NB
                )
                return True
            except portalocker.exceptions.LockException:
                if time.time() - start_time >= timeout:
                    logger.error("Failed to acquire lock within timeout")
                    return False
                time.sleep(0.1)

    def _release_lock(self, file_handle):
        """
        Release the lock on the file.

        Args:
            file_handle: Open file handle to unlock
        """
        try:
            portalocker.unlock(file_handle)
        except portalocker.exceptions.PortalockerError as e:
            logger.warning("Failed to release lock: %s", e)


    def _load_state(self):
        """
        Load warehouse state from the JSON file with file locking.
        If the file is missing or corrupted, start with an empty state.
        """
        try:
            if self.state_file.exists():
                with self.state_file.open('r') as f:
                    if self._acquire_lock(f):
                        try:
                            data = json.load(f)

                            if isinstance(data, dict):
                                # Basic sanity: ensure the structure is location -> item -> qty
                                self.state = {}
                                for loc_id, items in data.items():
                                    if isinstance(items, dict):
                                        self.state[str(loc_id)] = {
                                            str(item_id): int(qty)
                                            for item_id, qty in items.items()
                                        }
                                    else:
                                        self.state[str(loc_id)] = {}
                            else:
                                logger.warning(
                                    "State file has unexpected format, starting fresh."
                                )
                                self.state = {}
                        finally:
                            self._release_lock(f)
                    else:
                        logger.error("Could not acquire lock to load state")
                        self.state = {}
            else:
                self.state = {}
        except Exception as e:
            logger.error("Failed to load warehouse state: %s", e)
            self.state = {}

    def _save_state(self):
        """
        Save warehouse state to the JSON file atomically with file locking.
        """
        try:
            # Ensure parent directory exists
            self.state_file.parent.mkdir(parents=True, exist_ok=True)

            temp_file = self.state_file.with_suffix(
                self.state_file.suffix + '.tmp'
            )
            with temp_file.open('w') as f:
                if self._acquire_lock(f):
                    try:
                        json.dump(self.state, f, indent=2)
                        f.flush()
                        os.fsync(f.fileno())  # Ensure written to disk
                    finally:
                        self._release_lock(f)
                else:
                    logger.error("Could not acquire lock to save state")
                    return
            os.replace(temp_file, self.state_file)
        except Exception as e:
            logger.error("Failed to save warehouse state: %s", e)

    # -----------------------
    # Location operations
    # -----------------------

    def register_location(self, location_id):
        """
        Register a new location.

        Args:
            location_id (str): ID of the location.

        Returns:
            dict: status/message/output/error
        """
        try:
            self._load_state()

            if location_id in self.state:
                error_message = "Location '{}' already exists".format(
                    location_id
                )
                logger.error(error_message)
                return self._error_response(
                    "Failed to register location",
                    error_message
                )

            self.state[location_id] = {}
            self._save_state()

            return self._success_response(
                "Location '{}' registered successfully".format(location_id)
            )
        except Exception as e:
            error_message = "Exception while registering location '{}': {}".format(
                location_id, e
            )
            logger.error(error_message)
            return self._error_response("Failed to register location", error_message)

    def unregister_location(self, location_id):
        """
        Unregister an existing location (only if it has no inventory).

        Args:
            location_id (str): ID of the location.

        Returns:
            dict: status/message/output/error
        """
        try:
            self._load_state()

            if location_id not in self.state:
                error_message = "Location '{}' does not exist".format(
                    location_id
                )
                logger.error(error_message)
                return self._error_response(
                    "Failed to unregister location",
                    error_message
                )

            if self.state[location_id]:
                error_message = "Location '{}' has inventories".format(
                    location_id
                )
                logger.error(error_message)
                return self._error_response(
                    "Failed to unregister location",
                    error_message
                )

            del self.state[location_id]
            self._save_state()

            return self._success_response(
                "Location '{}' unregistered successfully".format(location_id)
            )
        except Exception as e:
            error_message = "Exception while unregistering location '{}': {}".format(
                location_id, e
            )
            logger.error(error_message)
            return self._error_response("Failed to unregister location", error_message)

    # -----------------------
    # Inventory operations
    # -----------------------

    def increment_inventory(self, location_id, item_id, quantity):
        """
        Add quantity to an item in a location.

        Args:
            location_id (str)
            item_id (str)
            quantity (int or str): quantity to add

        Returns:
            dict: status/message/output/error
        """
        try:
            self._load_state()

            if location_id not in self.state:
                error_message = "Location '{}' does not exist".format(
                    location_id
                )
                logger.error(error_message)
                return self._error_response(
                    "Failed to increment inventory",
                    error_message
                )

            try:
                quantity = int(quantity)
            except ValueError:
                error_message = "Quantity must be a valid integer"
                logger.error(error_message)
                return self._error_response(
                    "Failed to increment inventory",
                    error_message
                )

            if quantity <= 0:
                error_message = "Quantity must be positive"
                logger.error(error_message)
                return self._error_response(
                    "Failed to increment inventory",
                    error_message
                )

            current_qty = self.state[location_id].get(item_id, 0)
            new_qty = current_qty + quantity
            self.state[location_id][item_id] = new_qty
            self._save_state()

            return self._success_response(
                "Inventory incremented successfully",
                output={
                    'location_id': location_id,
                    'item_id': item_id,
                    'quantity': new_qty
                }
            )
        except Exception as e:
            error_message = "Exception while incrementing inventory: {}".format(e)
            logger.error(error_message)
            return self._error_response("Failed to increment inventory", error_message)

    def decrement_inventory(self, location_id, item_id, quantity):
        """
        Subtract quantity from an item in a location.

        Args:
            location_id (str)
            item_id (str)
            quantity (int or str): quantity to subtract

        Returns:
            dict: status/message/output/error
        """
        try:
            self._load_state()

            if location_id not in self.state:
                error_message = "Location '{}' does not exist".format(
                    location_id
                )
                logger.error(error_message)
                return self._error_response(
                    "Failed to decrement inventory",
                    error_message
                )

            if item_id not in self.state[location_id]:
                error_message = "Item '{}' does not exist in location '{}'".format(
                    item_id, location_id
                )
                logger.error(error_message)
                return self._error_response(
                    "Failed to decrement inventory",
                    error_message
                )

            try:
                quantity = int(quantity)
            except ValueError:
                error_message = "Quantity must be a valid integer"
                logger.error(error_message)
                return self._error_response(
                    "Failed to decrement inventory",
                    error_message
                )

            if quantity <= 0:
                error_message = "Quantity must be positive"
                logger.error(error_message)
                return self._error_response(
                    "Failed to decrement inventory",
                    error_message
                )

            current_qty = self.state[location_id][item_id]
            if current_qty < quantity:
                error_message = (
                    "Insufficient quantity of item '{}' in location '{}' (has {})"
                    .format(item_id, location_id, current_qty)
                )
                logger.error(error_message)
                return self._error_response(
                    "Failed to decrement inventory",
                    error_message
                )

            new_qty = current_qty - quantity
            if new_qty == 0:
                del self.state[location_id][item_id]
            else:
                self.state[location_id][item_id] = new_qty

            self._save_state()

            return self._success_response(
                "Inventory decremented successfully",
                output={
                    'location_id': location_id,
                    'item_id': item_id,
                    'quantity': new_qty
                }
            )
        except Exception as e:
            error_message = "Exception while decrementing inventory: {}".format(e)
            logger.error(error_message)
            return self._error_response("Failed to decrement inventory", error_message)

    def transfer_inventory(self, src_location, dest_location, item_id, quantity):
        """
        Transfer quantity of an item from one location to another.

        Args:
            src_location (str)
            dest_location (str)
            item_id (str)
            quantity (int or str)

        Returns:
            dict: status/message/output/error
        """
        try:
            self._load_state()

            if src_location not in self.state:
                error_message = "Location '{}' does not exist".format(
                    src_location
                )
                logger.error(error_message)
                return self._error_response(
                    "Failed to transfer inventory",
                    error_message
                )

            if dest_location not in self.state:
                error_message = "Location '{}' does not exist".format(
                    dest_location
                )
                logger.error(error_message)
                return self._error_response(
                    "Failed to transfer inventory",
                    error_message
                )

            if item_id not in self.state[src_location]:
                error_message = "Item '{}' does not exist in location '{}'".format(
                    item_id, src_location
                )
                logger.error(error_message)
                return self._error_response(
                    "Failed to transfer inventory",
                    error_message
                )

            try:
                quantity = int(quantity)
            except ValueError:
                error_message = "Quantity must be a valid integer"
                logger.error(error_message)
                return self._error_response(
                    "Failed to transfer inventory",
                    error_message
                )

            if quantity <= 0:
                error_message = "Quantity must be positive"
                logger.error(error_message)
                return self._error_response(
                    "Failed to transfer inventory",
                    error_message
                )

            src_qty = self.state[src_location][item_id]
            if src_qty < quantity:
                error_message = (
                    "Insufficient quantity of item '{}' in location '{}' (has {})"
                    .format(item_id, src_location, src_qty)
                )
                logger.error(error_message)
                return self._error_response(
                    "Failed to transfer inventory",
                    error_message
                )

            # Decrement from source
            new_src_qty = src_qty - quantity
            if new_src_qty == 0:
                del self.state[src_location][item_id]
            else:
                self.state[src_location][item_id] = new_src_qty

            # Increment at destination
            dest_qty = self.state[dest_location].get(item_id, 0)
            new_dest_qty = dest_qty + quantity
            self.state[dest_location][item_id] = new_dest_qty

            self._save_state()

            return self._success_response(
                "Inventory transferred successfully",
                output={
                    'src_location': src_location,
                    'dest_location': dest_location,
                    'item_id': item_id,
                    'src_quantity': new_src_qty,
                    'dest_quantity': new_dest_qty
                }
            )
        except Exception as e:
            error_message = "Exception while transferring inventory: {}".format(e)
            logger.error(error_message)
            return self._error_response("Failed to transfer inventory", error_message)

    # -----------------------
    # Query operations
    # -----------------------

    def observe_inventory(self, location_id):
        """
        Observe all inventory in a location.

        Args:
            location_id (str)

        Returns:
            dict: status/message/output/error
                  - output will be a dict of item_id -> quantity or 'EMPTY'
        """
        try:
            self._load_state()

            if location_id not in self.state:
                error_message = "Location '{}' does not exist".format(
                    location_id
                )
                logger.error(error_message)
                return self._error_response(
                    "Failed to observe inventory",
                    error_message
                )

            inventory = self.state[location_id]

            if not inventory:
                return self._success_response(
                    "Location '{}' has no inventory".format(location_id),
                    output='EMPTY'
                )

            # Sort items by item_id for deterministic output
            sorted_items = {
                item_id: inventory[item_id]
                for item_id in sorted(inventory.keys())
            }

            return self._success_response(
                "Inventory observed successfully",
                output=sorted_items
            )
        except Exception as e:
            error_message = "Exception while observing inventory: {}".format(e)
            logger.error(error_message)
            return self._error_response("Failed to observe inventory", error_message)
