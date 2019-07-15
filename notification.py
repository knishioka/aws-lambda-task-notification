import os
import base64
import boto3
from jira import JIRA
from slackclient import SlackClient
from functools import lru_cache


def main():
    overdue_filter_id = os.environ['JIRA_FILTER_OVERDUE']
    upcoming_filter_id = os.environ['JIRA_FILTER_UPCOMING']
    overdue_msg = task_summary(overdue_filter_id, '期限切れ')
    upcoming_msg = task_summary(upcoming_filter_id, '期限間近')
    slack_post(f'{overdue_msg}\n\n{upcoming_msg}')


@lru_cache(None)
def jira_connection():
    encrypted_id = os.environ['JIRA_ENCRYPTED_ID']
    encrypted_pass = os.environ['JIRA_ENCRYPTED_PASSWORD']
    jira_id = kms_decrypt(encrypted_id)
    jira_pass = kms_decrypt(encrypted_pass)
    options = {'server': os.environ['JIRA_SERVER']}
    return JIRA(options, basic_auth=(jira_id, jira_pass))


@lru_cache(None)
def slack_connection():
    encrypted_token = os.environ['SLACK_ENCRYPTED_TOKEN']
    slack_token = kms_decrypt(encrypted_token)
    return SlackClient(slack_token)


def is_active(user):
    return (user['is_bot'] is False and
            user['deleted'] is False and
            user['profile'].get('email') is not None)


def slack_post(msg):
    task_channel = os.environ['SLACK_CHANNEL_ID']
    slack_connection().api_call(
        "chat.postMessage",
        channel=task_channel,
        text=msg
    )


def format_task(task):
    f = task.fields
    assignee = f.assignee
    if assignee:
        mention = assignee.displayName
    else:
        mention = 'No Assignee'
    link = task.permalink()
    return f'{mention} [<{link}|{task.key}>] ({f.duedate}) {f.summary}'


def task_summary(filter_id, title):
    tasks = jira_connection().search_issues(f'filter={filter_id}')
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
