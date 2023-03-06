from deploy_feature_to_paas.app.copy_db import CopyDB


copy_db = CopyDB(
    space_name="monitoring-platform-test",
    db_name="monitoring-platform-default-db",
    path="./backup_for_AWS.sql"
)

copy_db.start()
