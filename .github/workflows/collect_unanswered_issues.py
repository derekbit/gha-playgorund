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
        'since': (datetime.utcnow() - timedelta(days=100)).isoformat() + 'Z'
    }
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    issues = response.json()
    return issues

def filter_issues(issues, team_members):
    filtered_issues = []
    for issue in issues:
        if 'pull_request' in issue:
            continue
        if issue['user']['login'] in team_members or issue['comments']:
            continue
        labels = [label['name'] for label in issue['labels']]
        if 'require/backport' not in labels:
            filtered_issues.append(issue)
    return filtered_issues

def get_team_members():
    org = "longhorn"
    team_slug = "dev"
    token = os.getenv('GITHUB_TOKEN')
    headers = {'Authorization': f'token {token}'}
    url = f"https://api.github.com/orgs/{org}/teams/{team_slug}/members"
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    members = response.json()
    team_members = [member['login'] for member in members]
    return team_members

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
    issues = get_issues()
    team_members = get_team_members()
    unanswered_issues = filter_issues(issues, team_members)
    send_to_slack(unanswered_issues)

if __name__ == "__main__":
    main()
