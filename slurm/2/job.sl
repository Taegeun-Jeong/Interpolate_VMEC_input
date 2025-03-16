#!/bin/bash
#SBATCH --job-name=desc2            # 잡 이름
#SBATCH --output=output2.log         # 표준 출력 파일
#SBATCH --error=error2.log          # 에러 로그 파일
#SBATCH --ntasks=1                   # 실행할 태스크 수
#SBATCH --cpus-per-task=1            # 태스크당 CPU 수
#SBATCH --time=00:00:00              # 최대 실행 시간 (HH:MM:SS)
#SBATCH --partition=all.q            # 파티션 이름
#SBATCH --nodelist=gpu01            # Specific node (if needed)
#SBATCH --dependency=afterok:2394    # 2394번 잡이 성공적으로 완료된 후에 실행

# Execute the main Python script
# python /home/taegeun/project/DESC_source/PPCF_revision_202503/make_interpolated_boundary/1_QA6_QH6_QI6/run_DESC_with_VMEC_input/run_VMEC.py
python /home/taegeun/project/DESC_source/PPCF_revision_202503/make_interpolated_boundary/2_QA6_QH8_QI8/run_DESC_with_VMEC_input/run_VMEC.py
# python /home/taegeun/project/DESC_source/PPCF_revision_202503/make_interpolated_boundary/3_QA6_QH8_QI6/run_DESC_with_VMEC_input/run_VMEC.py

# 완료 후 Slack 알림 (필요시)
python /home/taegeun/slurm/slack_send_notification.py "$SLURM_JOB_ID" "COMPLETED"
