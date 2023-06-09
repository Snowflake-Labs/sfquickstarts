#. /var/root/.aws/jzsun4

bucket='jsnow-vhol-assets'
region="us-west-2"

aws s3 sync ecs/ s3://$bucket/ecs/cfts/

aws cloudformation create-stack --stack-name ecs-sf-`date "+%s"` --disable-rollback --template-body file://ecs/main.json --capabilities CAPABILITY_IAM --capabilities CAPABILITY_NAMED_IAM --region $region
