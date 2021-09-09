# Pass the env-vars to MYCOMMAND
source .env
set +a
export AWS_DEFAULT_REGION="${AWS_DEFAULT_REGION_S3_STORE}"
export AWS_ACCESS_KEY_ID="${AWS_ACCESS_KEY_ID_S3_STORE}"
export AWS_SECRET_ACCESS_KEY="${AWS_SECRET_ACCESS_KEY_S3_STORE}"

if [ -f "./data/s3_files/20210604_auth_data.json" ] 
then
    echo "file exists"
else 
    aws s3 cp s3://paas-s3-broker-prod-lon-d9a58299-d162-49b5-8547-483663b17914/fixtures/20210604_auth_data.json ./data/s3_files/20210604_auth_data.json
fi


if [ -f "./data/s3_files/region_and_sector.json" ]
then
    echo "file exists"
else
    aws s3 cp s3://paas-s3-broker-prod-lon-d9a58299-d162-49b5-8547-483663b17914/fixtures/20210903_sector.json ./data/s3_files/20210903_sector.json
fi

if [ -f "./data/s3_files/pubsecweb_20210615.pgadmin-backup" ]
then
    echo "file exists"
else
    aws s3 cp s3://paas-s3-broker-prod-lon-d9a58299-d162-49b5-8547-483663b17914/pubsecweb/pubsecweb_20210615.pgadmin-backup ./data/s3_files/pubsecweb_20210615.pgadmin-backup
fi

if [ -f "./data/s3_files/a11ymon_mini_20210527.sql.zip" ]
then
    echo "file exists"
else
    aws s3 cp s3://paas-s3-broker-prod-lon-d9a58299-d162-49b5-8547-483663b17914/a11ymon/a11ymon_mini_20210527.sql.zip ./data/s3_files/a11ymon_mini_20210527.sql.zip
fi

if [ -f "./data/s3_files/a11ymon_mini_20210527.sql" ]
then
    echo "file exists"
else
    unzip -o ./data/s3_files/a11ymon_mini_20210527.sql.zip
fi
