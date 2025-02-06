# Knowledge Manager

The `knowledge_manager` is responsible for managing and retrieving knowledge data within the system. It utilizes AWS CDK for infrastructure management.

## Setup

Create a Python virtual environment for development:
```bash
python3 -m venv .venv
```
Activate the virtual environment:
```bash
source .venv/bin/activate
```
Install required dependencies:
```bash
pip install -r requirements.txt
```

## Useful Commands

- `cdk ls`: List all stacks in the app
- `cdk synth`: Emit the synthesized CloudFormation template
- `cdk deploy`: Deploy this stack to your default AWS account/region
- `cdk diff`: Compare deployed stack with current state
- `cdk docs`: Open CDK documentation

## Testing
To run tests, use:
```bash
python app_setup.py test
```

## Deployment
To deploy the application, use:
```bash
python app_setup.py deploy
```
For a faster deployment without installations or tests, use:
```bash
python app_setup.py fast_deploy
```

## Note

Ensure that the `aws-common` repository is cloned and updated as part of the setup process.
