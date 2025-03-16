#!/usr/bin/env python3
import re
import sys
import os

def parse_axis_line(line):
    """
    Parses a line containing axis parameters and returns a list of floats.
    Example line:
      RAXIS_CC = +1.03926952E+00 +2.00550127E-01 +2.34867075E-02 ...
    """
    parts = line.split('=', 1)
    if len(parts) != 2:
        return []
    values_str = parts[1].strip()
    # Extract all floating point numbers using regex
    values = re.findall(r'[+-]?\d+\.\d+E[+-]\d+', values_str)
    return [float(v) for v in values]

def format_axis_line(param, values):
    """
    Formats the axis parameter line with interpolated values.
    """
    formatted_values = ' '.join([f"{v:+.8E}" for v in values])
    return f"  {param} = {formatted_values}\n"

def parse_phiedge_line(line):
    """
    Parses a line containing PHIEDGE and returns its floating-point value.
    Example line:
      PHIEDGE = +4.00000000E-02
    """
    m = re.search(r'PHIEDGE\s*=\s*([+-]\d+\.\d+E[+-]\d+)', line)
    if m:
        return float(m.group(1))
    return None

def format_phiedge_line(value):
    """
    Formats the PHIEDGE line with the given value.
    """
    return f"  PHIEDGE = {value:+.8E}\n"

def parse_boundary_line(line):
    """
    Parses a boundary parameter line and returns the key and values.
    Example line:
      RBC(  0,  0) = +1.00000000E+00  ZBS(  0,  0) = +0.00000000E+00
    """
    pattern = re.compile(
        r'\s*RBC\(\s*(-?\d+),\s*(-?\d+)\)\s*=\s*([+-]?\d+\.\d+E[+-]\d+)\s+'
        r'ZBS\(\s*(-?\d+),\s*(-?\d+)\)\s*=\s*([+-]?\d+\.\d+E[+-]\d+)'
    )
    match = pattern.match(line)
    if not match:
        return None
    i1, j1, rbc_val, i2, j2, zbs_val = match.groups()
    if i1 != i2 or j1 != j2:
        raise ValueError("Mismatch in RBC and ZBS indices.")
    return ((int(i1), int(j1)), float(rbc_val), float(zbs_val))

def format_boundary_line(key, rbc, zbs):
    """
    Formats the boundary parameter line with given RBC and ZBS values.
    Uses a 2-character field for indices to match the original spacing.
    """
    i, j = key
    return f"  RBC( {i:2d}, {j:2d}) = {rbc:+.8E}  ZBS( {i:2d}, {j:2d}) = {zbs:+.8E}\n"

def read_parameters(filename):
    """
    Reads the axis parameters, boundary parameters, NTOR, and PHIEDGE from a file.
    Returns a tuple: (axis_params, boundary_params, ntor, phiedge)
      - axis_params: dictionary with keys 'RAXIS_CC' and 'ZAXIS_CS'
      - boundary_params: dictionary mapping (i, j) to (RBC, ZBS)
      - ntor: integer NTOR (or None if not found)
      - phiedge: floating-point PHIEDGE value (or None if not found)
    """
    axis_params = {}
    boundary_params = {}
    ntor = None
    phiedge = None
    with open(filename, 'r') as file:
        for line in file:
            # Look for NTOR
            if ntor is None and 'NTOR' in line:
                m = re.search(r'NTOR\s*=\s*(\d+)', line)
                if m:
                    ntor = int(m.group(1))
            # Look for PHIEDGE
            if phiedge is None and 'PHIEDGE' in line:
                phiedge = parse_phiedge_line(line)
            if 'RAXIS_CC' in line:
                axis_params['RAXIS_CC'] = parse_axis_line(line)
            elif 'ZAXIS_CS' in line:
                axis_params['ZAXIS_CS'] = parse_axis_line(line)
            elif 'RBC(' in line and 'ZBS(' in line:
                parsed = parse_boundary_line(line)
                if parsed:
                    key, rbc, zbs = parsed
                    boundary_params[key] = (rbc, zbs)
    return axis_params, boundary_params, ntor, phiedge

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
    
    # Read parameters from both input files.
    axis1, boundary1, ntor1, phiedge1 = read_parameters(file1)
    axis2, boundary2, ntor2, phiedge2 = read_parameters(file2)
    
    # Set NTOR to the minimum NTOR among the two input files.
    if ntor1 is None and ntor2 is None:
        min_ntor = None
    elif ntor1 is None:
        min_ntor = ntor2
    elif ntor2 is None:
        min_ntor = ntor1
    else:
        min_ntor = min(ntor1, ntor2)
    
    # Ensure that both files have PHIEDGE defined.
    if phiedge1 is None or phiedge2 is None:
        sys.exit("Error: PHIEDGE must be defined in both input files.")
    
    # Verify that both files have the same number of axis values.
    for param in ['RAXIS_CC', 'ZAXIS_CS']:
        if param not in axis1 or param not in axis2:
            sys.exit(f"Error: {param} not found in both input files.")
        if len(axis1[param]) != len(axis2[param]):
            sys.exit(f"Error: {param} has different number of values in the two files.")
    
    # Collect union of boundary keys from both files.
    all_keys = set(boundary1.keys()).union(set(boundary2.keys()))
    
    # Generate output files for each interpolation step.
    # The interpolation parameter w will go from 0 (file1) to 1 (file2).
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
        
        # Interpolate boundary parameters (using union of keys, missing values treated as 0).
        interp_boundary = {}
        for key in all_keys:
            rbc1, zbs1 = boundary1.get(key, (0.0, 0.0))
            rbc2, zbs2 = boundary2.get(key, (0.0, 0.0))
            interp_boundary[key] = (weight1 * rbc1 + weight2 * rbc2,
                                      weight1 * zbs1 + weight2 * zbs2)
        
        # Define the output filename.
        output_filename = f"{output_base}{step}"
        
        # Use file1 as a template for the remaining parts.
        with open(file1, 'r') as fin, open(output_filename, 'w') as fout:
            for line in fin:
                if 'RAXIS_CC' in line:
                    fout.write(format_axis_line('RAXIS_CC', interp_axis['RAXIS_CC']))
                elif 'ZAXIS_CS' in line:
                    fout.write(format_axis_line('ZAXIS_CS', interp_axis['ZAXIS_CS']))
                elif 'PHIEDGE' in line:
                    fout.write(format_phiedge_line(interp_phiedge))
                elif 'NTOR' in line:
                    fout.write(f"  NTOR = {min_ntor}\n")
                elif 'RBC(' in line and 'ZBS(' in line:
                    parsed = parse_boundary_line(line)
                    if parsed:
                        key, _, _ = parsed
                        if key in interp_boundary:
                            rbc_interp, zbs_interp = interp_boundary[key]
                            fout.write(format_boundary_line(key, rbc_interp, zbs_interp))
                        else:
                            fout.write(line)
                    else:
                        fout.write(line)
                else:
                    fout.write(line)
        print(f"Created {output_filename}")
    
    print("All interpolated files have been created (with NTOR set to the minimum of the two inputs).")

if __name__ == "__main__":
    main()
