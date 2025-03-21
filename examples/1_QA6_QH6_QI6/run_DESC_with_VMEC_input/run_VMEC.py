import os

index = 1
dir = "/home/taegeun/project/DESC_source/PPCF_revision_202503/make_interpolated_boundary/examples/1_QA6_QH6_QI6"
for num in range(0, 16):  # 15부터 0까지 감소하는 range
    for i in range(num + 1):
        command = f"python -m desc --gpu -vv {dir}/output/input.eq{index}_{num}_{i} -o {dir}/run_DESC_with_VMEC_input/output_hdf5/EQ_{index}_{num}_{i}.h5"
        os.system(command)