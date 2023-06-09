. /var/root/.aws/jzsun4

bucket='jsnow-vhol-assets'
region="us-west-2"

aws s3 sync ecs/ s3://$bucket/ecs/cfts/

aws cloudformation create-stack --stack-name ecs-sf-`date "+%s"` --parameters ParameterKey=SnowflakeUser,ParameterValue=streaming_user ParameterKey=SnowflakePassword,ParameterValue=Test1234567 ParameterKey=SnowflakeAccount,ParameterValue=zab91778.us-east-1 --disable-rollback --template-body file://ecs/main.json --capabilities CAPABILITY_IAM --capabilities CAPABILITY_NAMED_IAM --region $region
