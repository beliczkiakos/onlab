import re
import sys
import os

def parse_refinery_instance(ref_text):
    lanes = set()
    cars = set()
    car_positions = {}
    lane_dict = {}

    for line in ref_text.splitlines():
        line = line.strip()

        # Capture Lane declarations
        if line.startswith("type("):
            lane_id = line.split("(")[1].rstrip(").")
            lane_id_split = lane_id.split(",")
            lane_dict.update({lane_id_split[0].strip().replace("_n", "-"): lane_id_split[1].strip()})

        # Capture Car declarations
        elif line.startswith("Car("):
            car_id = line.split("(")[1].rstrip(").")
            cars.add(car_id)

        # Capture position(car, lane)
        elif line.startswith("position("):
            match = re.match(r"position\(([^,]+),\s*([^\)]+)\)\.", line)
            if match:
                car_id, lane_id = match.groups()
                car_positions[car_id] = lane_id.strip().replace("_n", "-")

    return lane_dict, sorted(cars), car_positions

def generate_scenic_code(cars, car_positions, lane_dict):
    scenic_lines = []
    scenic_lines.append(f"param map = localPath('../../assets/maps/CARLA/Town03.xodr')")
    scenic_lines.append(f"model scenic.simulators.carla.model")
    lanedict = {}
    # Define lane positions
    it = 0
    for lane_id in car_positions.values():
        lane_id_split = lane_id.split('_')
        if lane_dict.get(lane_id) == "driving":
            if "-" in lane_id_split[2]:
                scenic_lines.append(f"lane{it} = network.elements['{lane_id_split[0]}'].sections[{lane_id_split[1][-1]}].backwardLanes[{int(lane_id_split[2][-1]) - 1}]")
            else:    
                scenic_lines.append(f"lane{it} = network.elements['{lane_id_split[0]}'].sections[{lane_id_split[1][-1]}].forwardLanes[{lane_id_split[2][-1]}]")
        elif lane_dict.get(lane_id) == "shoulder":
            if "-" in lane_id_split[2]:
                scenic_lines.append(f"lane{it} = network.elements['{lane_id_split[0]}'].laneGroups[1].shoulder")
            else:
                scenic_lines.append(f"lane{it} = network.elements['{lane_id_split[0]}'].laneGroups[0].shoulder")
        elif lane_dict.get(lane_id) == "sidewalk":
            if "-" in lane_id_split[2]:
                scenic_lines.append(f"lane{it} = network.elements['{lane_id_split[0]}'].laneGroups[1].sidewalk")
            else:
                scenic_lines.append(f"lane{it} = network.elements['{lane_id_split[0]}'].laneGroups[0].sidewalk")
        elif lane_dict.get(lane_id) == "none":
            scenic_lines.append(f"lane{it} = network.elements['{lane_id_split[0]}'].sections[{lane_id_split[1][-1]}].forwardLanes[{lane_id_split[2][-1]}]")
        lanedict_value = f"lane{it}"
        lanedict.update({lane_id : lanedict_value})
        it += 1

    scenic_lines.append("")

    # Add car placements
    for i, car_id in enumerate(cars):
        lane_id = car_positions.get(car_id)
        if lane_id:
            car_def = "ego" if i == 0 else f"car{i}"
            scenic_lines.append(f"{car_def} = new Car on {lanedict.get(lane_id)}")

    return "\n".join(scenic_lines)

def convert_refinery_to_scenic(ref_text):
    lane_dict, cars, car_positions = parse_refinery_instance(ref_text)
    scenic_code = generate_scenic_code(cars, car_positions, lane_dict)
    return scenic_code

def main():
    if len(sys.argv) != 2:
        print("Usage: python converter.py <input_file.refinery>")
        sys.exit(1)

    input_file = sys.argv[1]
    if not os.path.isfile(input_file):
        print(f"Error: File '{input_file}' does not exist.")
        sys.exit(1)

    with open(input_file, 'r') as f:
        ref_text = f.read()

    scenic_code = convert_refinery_to_scenic(ref_text)

    output_file = os.path.splitext(input_file)[0] + ".scenic"
    with open(output_file, 'w') as f:
        f.write(scenic_code)

    print(f"Scenic code written to {output_file}")

if __name__ == "__main__":
    main()
