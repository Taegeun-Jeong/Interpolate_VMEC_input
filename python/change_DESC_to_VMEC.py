from desc import set_device
set_device("cpu")

import desc.io
from desc.vmec import VMECIO

"""
# run 1,2,3
dir1 = "/home/taegeun/project/DESC_source/PPCF_revision_202503/make_interpolated_boundary/1_QA6_QH6_QI6/run_DESC_with_VMEC_input/"
dir2 = "/home/taegeun/project/DESC_source/PPCF_revision_202503/make_interpolated_boundary/2_QA6_QH8_QI8/run_DESC_with_VMEC_input/"
dir3 = "/home/taegeun/project/DESC_source/PPCF_revision_202503/make_interpolated_boundary/3_QA6_QH8_QI6/run_DESC_with_VMEC_input/"
directories = [dir1, dir2, dir3]

for k, directory in enumerate(directories):
    for i in range(16):
        for j in range(i+1):
            print(f"\nEQ_{k+1}_{i}_{j}")
            try:
                eq = None
                eq = desc.io.load(directory + "output_hdf5/" + f"EQ_{k+1}_{i}_{j}.h5")[-1]
                VMECIO.save(eq, directory + "output_nc/" + f"wout_EQ_{k+1}_{i}_{j}.nc")
            except Exception as e:
                print(f"Error encountered for i={i}, j={j}: {e}")


# Exceptionally run 2 again.
directory = dir2
k=1
for i in range(16):
    for j in range(i+1):
        print(f"\nEQ_{k+1}_{i}_{j}")
        try:
            eq = None
            eq = desc.io.load(directory + "output_hdf5/" + f"EQ_{k+1}_{i}_{j}.h5")[-1]
            VMECIO.save(eq, directory + "output_nc/" + f"wout_EQ_{k+1}_{i}_{j}.nc")
        except Exception as e:
            print(f"Error encountered for i={i}, j={j}: {e}")

"""
# Exceptionally run 4.
directory = "/home/taegeun/project/DESC_source/PPCF_revision_202503/make_interpolated_boundary/examples/1_QA6_QH6_QI6/run_DESC_with_VMEC_input/"
k=1
for i in range(11, 16):
    for j in range(i+1):
        print(f"\nEQ_{k}_{i}_{j}")
        try:
            eq = None
            eq = desc.io.load(directory + "output_hdf5/" + f"EQ_{k}_{i}_{j}.h5")[-1]
            VMECIO.save(eq, directory + "output_nc/" + f"wout_EQ_{k}_{i}_{j}.nc")
        except Exception as e:
            print(f"Error encountered for i={i}, j={j}: {e}")