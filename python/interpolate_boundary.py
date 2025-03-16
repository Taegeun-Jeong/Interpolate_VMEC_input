#!/usr/bin/env python3
import re
import sys
import os

def parse_axis_line(line):
    """
    Parses a line containing an axis parameter and returns a list of floats.
    Example: "  RAXIS_CC = +1.01964961E+00 +1.97056327E-01 ..."
    """
    parts = line.split('=', 1)
    if len(parts) != 2:
        return []
    values_str = parts[1].strip()
    values = re.findall(r'[+-]?\d+\.\d+E[+-]\d+', values_str)
    return [float(v) for v in values]

def format_axis_line(param, values):
    formatted_values = ' '.join([f"{v:+.8E}" for v in values])
    return f"  {param} = {formatted_values}\n"

def parse_phiedge_line(line):
    """
    Parses a PHIEDGE line and returns the floating-point value.
    Example: "  PHIEDGE = +8.70000000E-02"
    """
    m = re.search(r'PHIEDGE\s*=\s*([+-]\d+\.\d+E[+-]\d+)', line)
    if m:
        return float(m.group(1))
    return None

def format_phiedge_line(value):
    return f"  PHIEDGE = {value:+.8E}\n"

def parse_boundary_line(line):
    """
    Parses a boundary line in the format:
      RBC(  i,  j) = <value>  ZBS(  i,  j) = <value>
    Returns a tuple: ((i, j), rbc_value, zbs_value)
    """
    pattern = r'RBC\(\s*(-?\d+),\s*(-?\d+)\)\s*=\s*([+-]\d+\.\d+E[+-]\d+)\s+ZBS\(\s*(-?\d+),\s*(-?\d+)\)\s*=\s*([+-]\d+\.\d+E[+-]\d+)'
    m = re.search(pattern, line)
    if m:
        i1, j1, rbc_val, i2, j2, zbs_val = m.groups()
        if i1 != i2 or j1 != j2:
            raise ValueError("Mismatch in RBC and ZBS indices.")
        return ((int(i1), int(j1)), float(rbc_val), float(zbs_val))
    return None

# Recommended modification for formatting
def format_boundary_line(key, rbc, zbs):
    i, j = key
    return f"  RBC({i:3d},{j:3d}) = {rbc:+.8E}  ZBS({i:3d},{j:3d}) = {zbs:+.8E}\n"

def read_parameters(filename):
    """
    Reads axis parameters, NTOR, PHIEDGE, and boundary parameters.
    In addition to returning the boundary dictionary,
    we also return a list (boundary_order) with the order of boundary keys
    as they appear in the file.
    """
    axis_params = {}
    boundary_params = {}
    boundary_order = []
    ntor = None
    phiedge = None
    with open(filename, 'r') as file:
        for line in file:
            # Check for NTOR
            if ntor is None and 'NTOR' in line:
                m = re.search(r'NTOR\s*=\s*(\d+)', line)
                if m:
                    ntor = int(m.group(1))
            # Check for PHIEDGE
            if phiedge is None and 'PHIEDGE' in line:
                phiedge = parse_phiedge_line(line)
            if 'RAXIS_CC' in line:
                axis_params['RAXIS_CC'] = parse_axis_line(line)
            elif 'ZAXIS_CS' in line:
                axis_params['ZAXIS_CS'] = parse_axis_line(line)
            elif 'RBC(' in line and 'ZBS(' in line:
                parsed = parse_boundary_line(line)
                if parsed:
                    key, rbc_val, zbs_val = parsed
                    # Only add to order list if not already present.
                    if key not in boundary_params:
                        boundary_order.append(key)
                    boundary_params[key] = (rbc_val, zbs_val)
    return axis_params, boundary_params, ntor, phiedge, boundary_order

def main():
    if len(sys.argv) != 5:
        sys.exit("Usage: python interpolate_boundary.py input.eq1 input.eq2 output_base n")
    file1 = sys.argv[1]
    file2 = sys.argv[2]
    output_base = sys.argv[3]
    try:
        total_files = int(sys.argv[4])
    except ValueError:
        sys.exit("Error: n must be an integer.")
    if total_files < 2:
        sys.exit("Error: n must be at least 2.")

    # Read parameters and boundary order from both input files.
    axis1, boundary1, ntor1, phiedge1, order1 = read_parameters(file1)
    axis2, boundary2, ntor2, phiedge2, order2 = read_parameters(file2)

    # Use maximum NTOR from both files.
    if ntor1 is None and ntor2 is None:
        max_ntor = None
    elif ntor1 is None:
        max_ntor = ntor2
    elif ntor2 is None:
        max_ntor = ntor1
    else:
        max_ntor = max(ntor1, ntor2)

    # Ensure both files define PHIEDGE.
    if phiedge1 is None or phiedge2 is None:
        sys.exit("Error: PHIEDGE must be defined in both input files.")

    # Verify axis parameters are present and consistent.
    for param in ['RAXIS_CC', 'ZAXIS_CS']:
        if param not in axis1 or param not in axis2:
            sys.exit(f"Error: {param} not found in both input files.")
        if len(axis1[param]) != len(axis2[param]):
            sys.exit(f"Error: {param} has different number of values in the two files.")

    # Determine the template order from the file with more boundary keys.
    if len(order2) >= len(order1):
        template_order = order2
    else:
        template_order = order1

    # Compute the union of boundary keys.
    union_keys = set(boundary1.keys()).union(set(boundary2.keys()))
    # Append keys that are missing in the template order.
    missing_keys = union_keys - set(template_order)
    # For these missing keys, sort them numerically.
    missing_keys_sorted = sorted(missing_keys, key=lambda key: (key[0], key[1]))
    # Final order: template order from the higher-mode file, then the missing keys.
    final_order = template_order + missing_keys_sorted

    # Read the entire content of file1 as a template.
    with open(file1, 'r') as f:
        file1_lines = f.readlines()

    # Generate output files for each interpolation step.
    for step in range(total_files):
        w = step / (total_files - 1)
        weight1 = 1.0 - w
        weight2 = w

        # Interpolate axis parameters.
        interp_axis = {}
        for param in ['RAXIS_CC', 'ZAXIS_CS']:
            values1 = axis1[param]
            values2 = axis2[param]
            interp_axis[param] = [weight1 * v1 + weight2 * v2 for v1, v2 in zip(values1, values2)]

        # Interpolate PHIEDGE.
        interp_phiedge = weight1 * phiedge1 + weight2 * phiedge2

        # Interpolate boundary parameters.
        interp_boundary = {}
        for key in final_order:
            rbc1, zbs1 = boundary1.get(key, (0.0, 0.0))
            rbc2, zbs2 = boundary2.get(key, (0.0, 0.0))
            rbc_interp = weight1 * rbc1 + weight2 * rbc2
            zbs_interp = weight1 * zbs1 + weight2 * zbs2
            interp_boundary[key] = (rbc_interp, zbs_interp)

        # Process the template file to replace parameters and boundaries.
        new_lines = []
        in_boundary_section = False
        for line in file1_lines:
            # Detect the start of the boundary section.
            if line.strip().startswith("!---- Boundary Parameters ----"):
                in_boundary_section = True
                new_lines.append(line)
                # Write out the full set of boundaries in the final order.
                for key in final_order:
                    rbc_interp, zbs_interp = interp_boundary[key]
                    new_lines.append(format_boundary_line(key, rbc_interp, zbs_interp))
                continue
            # If we are within the boundary section and the line looks like a boundary line, skip it.
            if in_boundary_section and ("RBC(" in line and "ZBS(" in line):
                continue
            # Exit boundary section if a new section starts.
            if in_boundary_section and line.strip().startswith("!") and not line.strip().startswith("!---- Boundary Parameters ----"):
                in_boundary_section = False
            # Replace axis, PHIEDGE, and NTOR lines when found.
            if 'RAXIS_CC' in line:
                new_lines.append(format_axis_line('RAXIS_CC', interp_axis['RAXIS_CC']))
            elif 'ZAXIS_CS' in line:
                new_lines.append(format_axis_line('ZAXIS_CS', interp_axis['ZAXIS_CS']))
            elif 'PHIEDGE' in line:
                new_lines.append(format_phiedge_line(interp_phiedge))
            elif 'NTOR' in line and max_ntor is not None:
                new_lines.append(f"  NTOR = {max_ntor}\n")
            else:
                new_lines.append(line)

        output_filename = f"{output_base}{step}"         # It's modified here.
        with open(output_filename, 'w') as fout:
            fout.writelines(new_lines)
        print(f"Created {output_filename}")

    print("All interpolated files have been created.")

if __name__ == "__main__":
    main()
