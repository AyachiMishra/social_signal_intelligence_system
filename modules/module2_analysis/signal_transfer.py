import json
import os

def transfer_signals(source_file, destination_file):
    # 1. Read data from the temporary source file
    if not os.path.exists(source_file):
        print(f"Error: {source_file} not found. Nothing to transfer.")
        return

    try:
        with open(source_file, 'r') as f:
            new_signals = json.load(f)
            # Ensure we are working with a list
            if not isinstance(new_signals, list):
                new_signals = [new_signals]
    except (json.JSONDecodeError, ValueError):
        print(f"Source file {source_file} is empty or invalid. Skipping.")
        return

    # 2. Load existing data from the final output file
    final_data = []
    if os.path.exists(destination_file):
        try:
            with open(destination_file, 'r') as f:
                final_data = json.load(f)
                if not isinstance(final_data, list):
                    final_data = [final_data]
        except json.JSONDecodeError:
            print(f"Warning: {destination_file} was corrupted. Starting fresh.")
            final_data = []

    # 3. Merge and Save to the final destination
    # We use .extend() to add the new list of items to the existing list
    final_data.extend(new_signals)
    
    with open(destination_file, 'w') as f:
        json.dump(final_data, f, indent=4)
    
    print(f"Successfully transferred {len(new_signals)} signals to {destination_file}.")

    # 4. Wipe the temporary source file (signals_output.json)
    with open(source_file, 'w') as f:
        json.dump([], f)
    print(f"Temporary file {source_file} has been wiped.")

if __name__ == "__main__":
    SOURCE = "signals_output.json"
    DESTINATION = "signals_final_output.json"
    
    transfer_signals(SOURCE, DESTINATION)