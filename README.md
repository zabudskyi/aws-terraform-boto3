# aws-terraform-boto3
This project shows how easily we can setup AWS environment with terraform and deal with it with AWS sdk for python - boto3.
### Prerequisites 
- [aws configure](https://docs.aws.amazon.com/cli/latest/reference/configure/)
- [terraform](https://www.terraform.io/)
- [boto3](http://boto3.readthedocs.io)
- [PrettyTable](https://pypi.python.org/pypi/PrettyTable)

## Setup your environment with terraform AWS provider
Fill `terraform/variables.tf.example` with your data and rename it to `variable.tf`

Run `terraform apply` and your environment is up and running in a minute. Just open your browser and go to `a.domain.name`. Awesome website, isn't it? 

## AWS sdk for python - boto3
run `./run.py --hosts your a.domain.name b.domain.name c.domain.name` and have a look at your environment up and running. 

Stop one or more instances. Image(s) of it(them) will be created and instance(s) will be terminated.

Wait 7 days and Image(s) will disappear as well. 

## Things to do 
- Deal with Exception `Instance is not in state 'running' or 'stopped'` when we run script too fast and Ec2 instance is still creating
- Deal with case when `run.py` is run with host that can be resolved but doesn't belong to our environment
- Add Elastic IP release code
- You are most welcome to add items to this list or/and criticize the code