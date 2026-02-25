#!/usr/bin/env python3
"""
Warehouse Management Tool - CLI Interface

Processes warehouse commands from stdin and outputs results to stdout.
Supports concurrent access via file locking.
"""
from setup_loader import logger
import sys
from modules.Warehouse import Warehouse


class WarehouseCLI:
    """Command-line interface for the Warehouse Management Tool."""

    def __init__(self, state_file=None):
        """
        Initialize the CLI with a Warehouse instance.

        Args:
            state_file (str, optional): Path to the state file
        """
        self.warehouse = Warehouse(state_file=state_file)

    def parse_command(self, line):
        """
        Parse a command line into command parts.

        Args:
            line (str): Command line from stdin

        Returns:
            list: Command parts, or None if invalid
        """
        parts = line.strip().split()
        if not parts:
            return None
        return parts

    def execute_command(self, parts):
        """
        Execute a parsed command and return the output.

        Args:
            parts (list): Command parts

        Returns:
            str: Output to write to stdout
        """
        if not parts:
            return ""

        # LOCATION commands
        if parts[0] == "LOCATION":
            if len(parts) < 3:
                return "ERR: Invalid LOCATION command format"

            action = parts[1]
            location_id = parts[2]

            if action == "REGISTER":
                result = self.warehouse.register_location(location_id)
                if result['status']:
                    return "OK"
                else:
                    return f"ERR: {result['error']}"

            elif action == "UNREGISTER":
                result = self.warehouse.unregister_location(location_id)
                if result['status']:
                    return "OK"
                else:
                    return f"ERR: {result['error']}"

            else:
                return f"ERR: Unknown LOCATION action '{action}'"

        # INVENTORY commands
        elif parts[0] == "INVENTORY":
            if len(parts) < 3:
                return "ERR: Invalid INVENTORY command format"

            action = parts[1]

            if action == "INCREMENT":
                if len(parts) != 5:
                    return "ERR: INCREMENT requires <LOCATION_ID> <ITEM_ID> <QUANTITY>"
                location_id = parts[2]
                item_id = parts[3]
                quantity = parts[4]
                result = self.warehouse.increment_inventory(
                    location_id, item_id, quantity)
                if result['status']:
                    return "OK"
                else:
                    return f"ERR: {result['error']}"

            elif action == "DECREMENT":
                if len(parts) != 5:
                    return "ERR: DECREMENT requires <LOCATION_ID> <ITEM_ID> <QUANTITY>"
                location_id = parts[2]
                item_id = parts[3]
                quantity = parts[4]
                result = self.warehouse.decrement_inventory(
                    location_id, item_id, quantity)
                if result['status']:
                    return "OK"
                else:
                    return f"ERR: {result['error']}"

            elif action == "TRANSFER":
                if len(parts) != 6:
                    return "ERR: TRANSFER requires <SRC_LOCATION> <DEST_LOCATION> <ITEM_ID> <QUANTITY>"
                src_location = parts[2]
                dest_location = parts[3]
                item_id = parts[4]
                quantity = parts[5]
                result = self.warehouse.transfer_inventory(
                    src_location, dest_location, item_id, quantity)
                if result['status']:
                    return "OK"
                else:
                    return f"ERR: {result['error']}"

            elif action == "OBSERVE":
                if len(parts) != 3:
                    return "ERR: OBSERVE requires <LOCATION_ID>"
                location_id = parts[2]
                result = self.warehouse.observe_inventory(location_id)
                if result['status']:
                    output = result['output']
                    if output == 'EMPTY':
                        return "EMPTY"
                    else:
                        # Format as "ITEM <item_id> <quantity>" for each item
                        lines = []
                        for item_id in sorted(output.keys()):
                            lines.append(f"ITEM {item_id} {output[item_id]}")
                        return "\n".join(lines)
                else:
                    return f"ERR: {result['error']}"

            else:
                return f"ERR: Unknown INVENTORY action '{action}'"

        else:
            return f"ERR: Unknown command '{parts[0]}'"

    def run(self):
        """
        Main loop: read commands from stdin, execute, and write to stdout.
        """
        logger.info("Warehouse CLI started")
        try:
            for line in sys.stdin:
                line = line.strip()
                if not line:
                    continue

                logger.debug(f"Processing command: {line}")
                parts = self.parse_command(line)

                if parts is None:
                    continue

                output = self.execute_command(parts)
                print(output)
                sys.stdout.flush()  # Ensure output is written immediately

        except KeyboardInterrupt:
            logger.info("Warehouse CLI interrupted by user")
            print("\nShutting down...", file=sys.stderr)
            sys.exit(0)
        except Exception as e:
            logger.error(f"Unexpected error in CLI: {e}")
            print(f"ERR: Internal error - {e}", file=sys.stderr)
            sys.exit(1)
        finally:
            logger.info("Warehouse CLI stopped")


def main():
    """
    Entry point for the warehouse management tool.
    """
    cli = WarehouseCLI()
    cli.run()


if __name__ == '__main__':
    main()
