#!/usr/bin/env python3
import re
import sys

def parse_nfp(lines, target_nfp):
    """
    Find the NFP parameter, store original value, and replace it with the target_nfp.
    Returns the original NFP and modified lines.
    """
    pattern_nfp = re.compile(r'(NFP\s*=\s*)(\d+)')
    original_nfp = None
    new_lines = []
    for line in lines:
        match = pattern_nfp.search(line)
        if match:
            original_nfp = int(match.group(2))
            # Check if conversion is possible: original_nfp must be divisible by target_nfp
            if original_nfp % target_nfp != 0:
                sys.exit(f"Error: Cannot change NFP = {original_nfp} to NFP = {target_nfp} because {original_nfp} is not divisible by {target_nfp}.")
            # Replace with NFP = target_nfp while preserving spacing.
            line = pattern_nfp.sub(r'\g<1>' + str(target_nfp), line)
        new_lines.append(line)
    if original_nfp is None:
        sys.exit("Error: NFP parameter not found in the file.")
    return original_nfp, new_lines

def update_ntor(lines, original_nfp, target_nfp):
    """
    Update the NTOR parameter.
    If NTOR = k then new NTOR becomes k * (original_nfp / target_nfp).
    """
    pattern_ntor = re.compile(r'(NTOR\s*=\s*)(\d+)')
    new_lines = []
    ntor_found = False
    factor = original_nfp // target_nfp
    for line in lines:
        match = pattern_ntor.search(line)
        if match:
            ntor_found = True
            original_ntor = int(match.group(2))
            new_ntor = original_ntor * factor
            line = pattern_ntor.sub(r'\g<1>' + str(new_ntor), line)
        new_lines.append(line)
    if not ntor_found:
        print("Warning: NTOR parameter not found in the file.")
    return new_lines

def parse_boundary_section(lines):
    """
    Extract the boundary parameters section.
    Returns the starting index of the section, a list of boundary lines,
    and a list of any lines after the boundary definitions.
    """
    boundary_start_index = None
    for i, line in enumerate(lines):
        if line.strip().startswith("!---- Boundary Parameters"):
            boundary_start_index = i
            break
    if boundary_start_index is None:
        sys.exit("Error: Boundary Parameters section not found.")
    boundary_lines = []
    post_boundary_lines = []
    for line in lines[boundary_start_index+1:]:
        # Lines that contain both RBC( and ZBS( are taken as boundary coefficient definitions.
        if "RBC(" in line and "ZBS(" in line:
            boundary_lines.append(line)
        else:
            post_boundary_lines.append(line)
    return boundary_start_index, boundary_lines, post_boundary_lines

def process_boundaries(boundary_lines, factor):
    """
    Process each boundary parameter line.
    Each line is assumed to have the format:
      RBC(  n,  m) = <value>  ZBS(  n,  m) = <value>
    Multiply the first mode number by factor (which is original_NFP/target_NFP)
    and group coefficients by m.
    """
    pattern = re.compile(
        r'RBC\(\s*([-]?\d+)\s*,\s*([-]?\d+)\s*\)\s*=\s*([+\-]\d\.\d+E[+\-]\d+)\s+'
        r'ZBS\(\s*([-]?\d+)\s*,\s*([-]?\d+)\s*\)\s*=\s*([+\-]\d\.\d+E[+\-]\d+)'
    )
    # boundaries[m] maps the new Fourier index (n*factor) to (RBC_value, ZBS_value)
    boundaries = {}
    for line in boundary_lines:
        match = pattern.search(line)
        if match:
            n_str, m_str, rbc_val, n2_str, m2_str, zbs_val = match.groups()
            if m_str != m2_str:
                sys.exit(f"Error: Mismatch in m values in line: {line}")
            original_n = int(n_str)
            m = int(m_str)
            new_n = original_n * factor
            if m not in boundaries:
                boundaries[m] = {}
            boundaries[m][new_n] = (rbc_val, zbs_val)
        else:
            print("Warning: The following line did not match the expected format and will be skipped:")
            print(line)
    return boundaries

def fill_boundaries(boundaries):
    """
    For each m, fill in missing Fourier mode numbers between the minimum and maximum with zeros.
    Returns a list of formatted boundary lines.
    """
    output_lines = []
    # Process each m in ascending order
    for m in sorted(boundaries.keys()):
        n_modes = boundaries[m]
        all_n = sorted(n_modes.keys())
        min_n = all_n[0]
        max_n = all_n[-1]
        for new_n in range(min_n, max_n + 1):
            if new_n in n_modes:
                rbc_val, zbs_val = n_modes[new_n]
            else:
                rbc_val = "+0.00000000E+00"
                zbs_val = "+0.00000000E+00"
            line_out = f"  RBC({new_n:3d},{m:3d}) = {rbc_val}  ZBS({new_n:3d},{m:3d}) = {zbs_val}\n"
            output_lines.append(line_out)
    return output_lines

def main():
    if len(sys.argv) < 2:
        sys.exit("Usage: python modify_nfp.py <input_file> [target_nfp]")
    input_filename = sys.argv[1]
    target_nfp = int(sys.argv[2]) if len(sys.argv) > 2 else 1

    # Read all lines from the input file.
    with open(input_filename, 'r') as f:
        lines = f.readlines()
    
    # Parse and replace the NFP value with the user-defined target,
    # and capture the original NFP.
    original_nfp, lines = parse_nfp(lines, target_nfp)
    
    # Calculate the factor for converting Fourier mode indices.
    factor = original_nfp // target_nfp

    # Update NTOR accordingly.
    lines = update_ntor(lines, original_nfp, target_nfp)
    
    # Locate and process the boundary parameters section.
    boundary_start_index, boundary_lines, post_boundary_lines = parse_boundary_section(lines)
    boundaries = process_boundaries(boundary_lines, factor)
    new_boundary_lines = fill_boundaries(boundaries)
    
    # Reassemble the file.
    output_lines = lines[:boundary_start_index+1] + new_boundary_lines + post_boundary_lines
    
    # Write to a new file with the suffix "_modified_to_nfpX", where X is the target_nfp.
    output_filename = f"{input_filename}_modified_to_nfp{target_nfp}"
    with open(output_filename, 'w') as f:
        f.writelines(output_lines)
    
    print(f"Modified file written to {output_filename}")

if __name__ == "__main__":
    main()
