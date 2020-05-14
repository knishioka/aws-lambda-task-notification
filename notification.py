import os
import base64
import boto3
import json
from jira import JIRA
from slack import WebClient
from functools import lru_cache


def main():
    jql_list = json.loads(os.environ['JQL_LIST'])
    messages = [task_summary(jql_dict['jql'], jql_dict['title']) for jql_dict in jql_list]
    slack_post('\n\n'.join(messages))


@lru_cache(None)
def jira_connection():
    encrypted_id = os.environ['JIRA_ENCRYPTED_ID']
    encrypted_pass = os.environ['JIRA_ENCRYPTED_TOKEN']
    jira_id = kms_decrypt(encrypted_id)
    jira_pass = kms_decrypt(encrypted_pass)
    options = {'server': os.environ['JIRA_SERVER']}
    return JIRA(options, basic_auth=(jira_id, jira_pass))


@lru_cache(None)
def slack_connection():
    encrypted_token = os.environ['SLACK_ENCRYPTED_TOKEN']
    slack_token = kms_decrypt(encrypted_token)
    return WebClient(slack_token)


def is_active(user):
    return (user['is_bot'] is False
            and user['deleted'] is False
            and user['profile'].get('email') is not None)


def slack_post(msg):
    task_channel = os.environ['SLACK_CHANNEL_ID']
    slack_connection().chat_postMessage(
        channel=task_channel,
        text=msg
    )


def format_task(task):
    f = task.fields
    assignee = f.assignee
    if assignee:
        display_name = assignee.displayName
        if display_name in jira_slack_mapping():
            mention = f'<@{jira_slack_mapping()[display_name]}>'
        else:
            mention = display_name
    else:
        mention = 'No Assignee'
    link = task.permalink()
    return f'{mention} [<{link}|{task.key}>] ({f.duedate}) {f.summary}'


@lru_cache(None)
def jira_slack_mapping():
    mapping_key = 'JIRA_SLACK_MAPPING_JSON'
    if mapping_key in os.environ:
        return json.loads(os.environ[mapping_key])
    else:
        return {}


def task_summary(jql, title):
    tasks = jira_connection().search_issues(jql)
    if tasks:
        return f'{title}\n' + '\n'.join(map(format_task, tasks))
    else:
        return ''


def jira_tasks(filter_id):
    return jira_connection().search_issues(f'filter={filter_id}')


def kms_decrypt(encrypted_txt):
    ciphertext_blob = base64.b64decode(encrypted_txt)
    kms = boto3.client('kms')
    dec = kms.decrypt(CiphertextBlob=ciphertext_blob)
    return dec['Plaintext'].decode('utf-8')


if __name__ == '__main__':
    main()
