import os
from snowflake.ml.jobs import submit_file
from snowflake.ml.jobs._utils import constants
from snowflake.snowpark import Session

ROLE = "SYSADMIN"
DATABASE = "MULTINODE_MULTIGPU_MYDB"
SCHEMA = "AUDIO_TRANSCRIPTION_SCH"
WAREHOUSE = "ML_MODEL_WH"
COMPUTE_POOL = "audio_processing_cp_gpu_nv_s_5_nodes"
PAYLOAD_STAGE = "job_stage"

def main():
    # Create Snowflake session from default config
    # See: https://docs.snowflake.com/en/developer-guide/snowflake-cli/connecting/configure-connection
    session = Session.builder.getOrCreate()
    session.use_database(DATABASE)
    session.use_schema(SCHEMA)
    session.use_warehouse(WAREHOUSE)
    session.use_role(ROLE)

    # TEMPORARY: Set the container image tag to 1.6.2
    constants.DEFAULT_IMAGE_TAG = "1.6.2"

    # Submit the transcribe_audio.py script as an ML Job
    job = submit_file(
        os.path.join(os.path.dirname(__file__), "transcribe_audio.py"),
        compute_pool=COMPUTE_POOL,
        stage_name=PAYLOAD_STAGE,
        target_instances=5,
        min_instances=1,
        external_access_integrations=["ALLOW_ALL_INTEGRATION"],
        session=session,
    )
    print(f"Job submitted: {job.id}")

    # Wait for the job to complete
    status = job.wait()
    print(f"Job status: {status}")

    # Get the job output
    logs = job.get_logs()
    print(f"Job logs:\n{logs}")

if __name__ == "__main__":
    main()