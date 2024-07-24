import os
import requests
from datetime import datetime, timedelta

def get_project_issues():
    project_id = 5
    org = "longhorn"
    token = os.getenv('GITHUB_TOKEN')
    headers = {'Authorization': f'token {token}'}
    url = f"https://api.github.com/orgs/{org}/projects/{project_id}/columns"
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    columns = response.json()

    issues = []
    for column in columns:
        column_url = column['cards_url']
        column_response = requests.get(column_url, headers=headers)
        column_response.raise_for_status()
        cards = column_response.json()

        for card in cards:
            if 'content_url' in card and 'issues' in card['content_url']:
                issue_url = card['content_url']
                issue_response = requests.get(issue_url, headers=headers)
                issue_response.raise_for_status()
                issue = issue_response.json()
                issues.append(issue)

    return issues

def filter_issues(issues):
    filtered_issues = []
    maintainers = get_maintainers()
    for issue in issues:
        if 'pull_request' in issue:
            continue
        if issue['user']['login'] not in maintainers and not issue['comments']:
            labels = [label['name'] for label in issue['labels']]
            if 'require/backport' not in labels:
                filtered_issues.append(issue)
    return filtered_issues

def get_maintainers():
    repo = "longhorn/longhorn"
    token = os.getenv('GITHUB_TOKEN')
    headers = {'Authorization': f'token {token}'}
    url = f"https://api.github.com/repos/{repo}/collaborators"
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    collaborators = response.json()
    maintainers = [collab['login'] for collab in collaborators]
    return maintainers

def send_to_slack(issues):
    webhook_url = os.getenv('SLACK_WEBHOOK_URL')
    if not issues:
        message = "No unanswered issues found."
    else:
        message = "Unanswered Issues in the last 7 days:\n"
        for issue in issues:
            message += f"- {issue['title']} ({issue['html_url']})\n"
    
    payload = {
        "payload": message
    }
    
    headers = {
        'Content-Type': 'application/json'
    }

    response = requests.post(webhook_url, json=payload, headers=headers)
    response.raise_for_status()

def main():
    issues = get_project_issues()
    unanswered_issues = filter_issues(issues)
    send_to_slack(unanswered_issues)

if __name__ == "__main__":
    main()
