from matplotlib import pyplot as plt
import xml.etree.ElementTree as ET
import numpy as np


REDS = [
    '-X---X-XXXX--XXX---',
    '-X---X-X---X--X----',
    '-X---X-X---X--X----',
    '-X-X-X-XXXX---X----',
    '-X-X-X-X------X----',
    '-X-X-X-X------X----',
    '--X-X--X-----XXX---'
]

GREENS = [
    '-XX---XX---XX--XXXX',
    'X--X-X--X-X--X-X---',
    '---X-X--X----X-XXX-',
    '--X--X-XX---X-----X',
    '-X---XX-X--X------X',
    'X----X--X-X-------X',
    'XXXX--XX--XXXX-XXX-'
]

BLUES = [
    '-XXXXX--XXX--XXXXX-',
    '-X-----X---X-X-----',
    '-X-----X-----X-----',
    '-XXXX--X-----XXXX--',
    '-X-----X-----X-----',
    '-X-----X---X-X-----',
    '-XXXXX--XXX--XXXXX-'
]

CHAR_TO_INT = {
    'A': 0,
    'B': 1,
    'C': 2,
    'D': 3,
    'E': 4,
    'F': 5,
    'G': 6
}

INT_TO_CHAR = {
    0 : 'A', 
    1 : 'B', 
    2 : 'C', 
    3 : 'D', 
    4 : 'E', 
    5 : 'F', 
    6 : 'G' 
}

def parse_led_array(data):
    return np.array([[1 if c == 'X' else 0 for c in row] for row in data])

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
    
def check_sch_connections():
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
        print("Done printing errors")
    else:
        print("All LED connections are correct.")
    
def diode_str_to_int(name)->int:
    '''
    Given the name of an LED, e.g. "DA12", return the number associated with it, e.g. 12
    '''
    return int(name[2:])
    
def diode_name_to_xy_mm(name:str, start_coords:tuple, spacing:tuple):
    '''
    Given the name of an LED, e.g. "DA2", return its xy coordinates in mm given spacing
    and coordinates of the top left LED
    '''
    row_char = name[1]
    row = CHAR_TO_INT[row_char]
    col = diode_str_to_int(name) - 1
    
    led_x = start_coords[0] + spacing[0] * col
    led_y = start_coords[1] - spacing[1] * row
    
    return (led_x, led_y)
    
def place_leds(brd_path:str, all_leds:np.ndarray, start:tuple, spacing:tuple):
    
    # TODO: open the board file here
    # Parse the board XML file
    tree = ET.parse(brd_path)
    root = tree.getroot()

    # Locate the elements section
    elements_section = root.find(".//elements")
    if elements_section is None:
        raise RuntimeError("No <elements> section found in board file.")
    
    count_updated = 0
    
    for y_idx in range(len(all_leds)):
        for x_idx in range(len(all_leds[0])):
            
            # If there's an LED here, calculate its coordinates
            if(all_leds[y_idx, x_idx] == 1):
                led_name = 'D' + INT_TO_CHAR[y_idx] + f'{x_idx+1}'
                coordinates = diode_name_to_xy_mm(led_name, start, spacing)
                print(f"{led_name:>4} : ({coordinates[0]:>2}, {coordinates[1]:>2})")
                
                # TODO: find led_name in the board file, and update the coordinate with coordinates[0] and coordinates[1]
                # Search for the matching <element> tag
                for element in elements_section.findall("element"):
                    if element.get("name") == led_name:
                        element.set("x", str(coordinates[0]))
                        element.set("y", str(coordinates[1]))
                        count_updated += 1
                        break
                else:
                    print(f"Warning: LED {led_name} not found in board.")
   
    print(f"Updated {count_updated} LED positions.")
    
    # Write back to a new board file
    new_brd_path = brd_path.replace(".brd", "_updated.brd")
    tree.write(new_brd_path)
    print(f"Saved updated board to {new_brd_path}")
   
if __name__ == '__main__':
    
    # Convert data
    red_array = parse_led_array(REDS)
    green_array = parse_led_array(GREENS)
    blue_array = parse_led_array(BLUES)
    check_sch_connections()
    
    merged_leds = (red_array + green_array + blue_array)
    for row in range(len(merged_leds)):
        for col in range(len(merged_leds[0])):
            if(merged_leds[row,col] >=1 ):
                merged_leds[row,col] = 1
    
    # All coordinates in mm
    # Top left coordinates of DA1
    top_left = (3, 44) # x, y from bottom left of PCB
    spacing = (5,5)    
    place_leds('./reva.brd', merged_leds, top_left, spacing)
    
    

    # Create plots of the arrays
    # plt.figure(figsize=(10, 4))
    # plt.subplot(1, 3, 1)
    # plot_led_matrix(red_array, 'Red LEDs', 'Reds')
    # plt.subplot(1, 3, 2)
    # plot_led_matrix(green_array, 'Green LEDs', 'Greens')
    # plt.subplot(1, 3, 3)
    # plot_led_matrix(blue_array, 'Blue LEDs', 'Blues')
    # plt.tight_layout()
    # plt.show()
    
    