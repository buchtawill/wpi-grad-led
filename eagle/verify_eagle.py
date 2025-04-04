from matplotlib import pyplot as plt
import xml.etree.ElementTree as ET
import numpy as np


REDS = [
    'p-X---X-XXXX--XXX---',
    'p-X---X-X---X--X----',
    'p-X---X-X---X--X----',
    'p-X-X-X-XXXX---X----',
    'p-X-X-X-X------X----',
    'p-X-X-X-X------X----',
    'p--X-X--X-----XXX---'
]

GREENS = [
    'p-XX---XX---XX--XXXX',
    'pX--X-X--X-X--X-X---',
    'p---X-X--X----X-XXX-',
    'p--X--X-XX---X-----X',
    'p-X---XX-X--X------X',
    'pX----X--X-X-------X',
    'pXXXX--XX--XXXX-XXX-'
]

BLUES = [
    'p-XXXXX--XXX--XXXXX-',
    'p-X-----X---X-X-----',
    'p-X-----X-----X-----',
    'p-XXXX--X-----XXXX--',
    'p-X-----X-----X-----',
    'p-X-----X---X-X-----',
    'p-XXXXX--XXX--XXXXX-'
]

def parse_led_array(data):
    return np.array([[1 if c == 'X' else 0 for c in row[1:]] for row in data])

# Plot function
def plot_led_matrix(array, title, cmap):
    plt.imshow(array, cmap=cmap, aspect='auto', interpolation='nearest')
    plt.title(title)
    plt.axis('off')
    
def extract_connections(sch_path):
    tree = ET.parse(sch_path)
    root = tree.getroot()
    
    connections = {}
    for net in root.findall(".//net"):
        net_name = net.get("name")
        for pinref in net.findall(".//pinref"):
            part = pinref.get("part")
            pin = pinref.get("pin")
            if part.startswith("D") and pin in {"R-", "G-", "B-"}:
                connections.setdefault(part, set()).add(pin)
    
    return connections

def validate_led_connections(led_matrix, connections, color):
    errors = []
    for row_idx, row in enumerate(led_matrix):
        row_label = chr(ord('A') + row_idx)
        for col_idx, led in enumerate(row):
            led_name = f"D{row_label}{col_idx + 1}"
            expected_net = f"{color}-"
            if led == 1:
                if led_name not in connections or expected_net not in connections[led_name]:
                    errors.append(f"{led_name} missing connection to {expected_net}")
            else:
                if led_name in connections and expected_net in connections[led_name]:
                    errors.append(f"{led_name} has erroneous connection to {expected_net}")
    return errors
    
if __name__ == '__main__':
    
    # Convert data
    red_array = parse_led_array(REDS)
    green_array = parse_led_array(GREENS)
    blue_array = parse_led_array(BLUES)

    # Load schematic connections
    schematic_path = "./reva.sch"
    connections = extract_connections(schematic_path)

    # Validate connections
    errors = []
    errors.extend(validate_led_connections(red_array, connections, "R"))
    errors.extend(validate_led_connections(green_array, connections, "G"))
    errors.extend(validate_led_connections(blue_array, connections, "B"))

    # Print errors if any
    if errors:
        print("Errors found:")
        for error in errors:
            print(error)
    else:
        print("All LED connections are correct.")

    # Create plots of the arrays
    plt.figure(figsize=(10, 4))
    plt.subplot(1, 3, 1)
    plot_led_matrix(red_array, 'Red LEDs', 'Reds')
    plt.subplot(1, 3, 2)
    plot_led_matrix(green_array, 'Green LEDs', 'Greens')
    plt.subplot(1, 3, 3)
    plot_led_matrix(blue_array, 'Blue LEDs', 'Blues')
    plt.tight_layout()
    plt.show()
    
    