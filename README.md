# aws lambda task notification
Notify jira tasks to slack via aws lambda.

NOTE: Removed converting JIRA user to slack user because JIRA API no longer provide user's email address.

# Encrpyt by KMS
```
aws kms encrypt --key-id <key id> --plaintext <text>
```

# Environment variables
- JIRA_SERVER: jira server url
- JIRA_ENCRYPTED_ID: Jira user id encrypted by aws kms
- JIRA_ENCRYPTED_TOKEN: Jira user token encrypted by aws kms
- SLACK_ENCRYPTED_TOKEN: slack token encrypted by aws kms
- SLACK_CHANNEL_ID: slack channel id
- JIRA_SLACK_MAPPING_JSON: mapping jira account key and slack member id
- JQL_LIST: jql and title list.

# Get Atlassian token
https://id.atlassian.com/manage/api-tokens

# Create aws lambda zip

```
cd package
pip install -r ../requirements.txt --target .
zip -r9 ../function.zip .
cd ../
zip -g function.zip notification_handler.py
zip -g function.zip notification.py
```


# Update lambda function
```
aws lambda update-function-code --function-name python37 --zip-file fileb://function.zip
```


# Run locally
```
JIRA_ENCRYPTED_ID=<your encrypted id> \
JIRA_ENCRYPTED_TOKEN=<your encrypted password> \
SLACK_ENCRYPTED_TOKEN=<your encrypted token> \
SLACK_CHANNEL_ID=<slack channel id> \
JQL_LIST='[{"jql": "filter = 1", "title": "filter 1"}, {"jql": "filter = 2", "title": "filter 2"}]' \
python notification.py
```
