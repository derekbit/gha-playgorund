import os
import requests
from datetime import datetime, timedelta

def get_issues():
    repo = "longhorn/longhorn"
    token = os.getenv('GITHUB_TOKEN')
    headers = {'Authorization': f'token {token}'}
    url = f"https://api.github.com/repos/{repo}/issues"
    params = {
        'state': 'open',
        'since': (datetime.utcnow() - timedelta(days=7)).isoformat() + 'Z'
    }
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    issues = response.json()
    return issues

def filter_issues(issues):
    filtered_issues = []
    maintainers = get_maintainers()
    for issue in issues:
        if 'pull_request' in issue:
            continue
        if issue['user']['login'] not in maintainers and not issue['comments']:
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
    response = requests.post(webhook_url, json={'text': message})
    response.raise_for_status()

def main():
    issues = get_issues()
    unanswered_issues = filter_issues(issues)
    send_to_slack(unanswered_issues)

if __name__ == "__main__":
    main()
