import requests
import os

GITHUB_ORG = "dereksu-org"
GITHUB_REPO = "gha-playground"
GITHUB_API_URL = "https://api.github.com"


ZENHUB_API_URL = "https://api.zenhub.com/p1/repositories/{repo_id}/board"
ZENHUB_ACCESS_TOKEN = os.getenv("ZENHUB_ACCESS_TOKEN")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_OWNER = "derekbit"
GITHUB_REPO = "gha-playground"
PROJECT_BOARD_ID = "66a8704553f5880017fe7d21"


def get_github_repo_id():
    url = f"{GITHUB_API_URL}/repos/{GITHUB_OWNER}/{GITHUB_REPO}"
    headers = {
        "Authorization": GITHUB_TOKEN
    }
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        return response.json().get("id")
    else:
        response.raise_for_status()


# def get_zenhub_board():
#     url = "https://api.zenhub.com/p1/repositories/830364723/board"
#     headers = {
#         "Content-Type": "application/json",
#         "X-Authentication-Token": ZENHUB_ACCESS_TOKEN
#     }

#     response = requests.get(url, headers=headers)

#     if response.status_code == 200:
#         return response.json()
#     else:
#         response.raise_for_status()


# def create_github_issue(title, body, labels):
#     url = f"{GITHUB_API_URL}/repos/{GITHUB_OWNER}/{GITHUB_REPO}/issues"
#     headers = {
#         "Authorization": f"Bearer {GITHUB_TOKEN}",
#         "Accept": "application/vnd.github.v3+json"
#     }
#     data = {
#         "title": title,
#         "body": body,
#         "labels": labels
#     }
#     response = requests.post(url, json=data, headers=headers)
#     response.raise_for_status()
#     return response.json()

# def add_issue_to_project(issue_id, column_id):
#     url = f"{GITHUB_API_URL}/projects/columns/{column_id}/cards"
#     headers = {
#         "Authorization": f"Bearer {GITHUB_TOKEN}",
#         "Accept": "application/vnd.github.inertia-preview+json"
#     }
#     data = {
#         "content_id": issue_id,
#         "content_type": "Issue"
#     }
#     response = requests.post(url, json=data, headers=headers)
#     response.raise_for_status()
#     return response.json()


def sync_tickets():
    repo_id = get_github_repo_id()
    print(repo_id)
    
    # for pipeline in board['pipelines']:
    #     column_id = None
    #     if pipeline['name'] == 'New Issues':
    #         column_id = 'your_new_issues_column_id'
    #     elif pipeline['name'] == 'Icebox':
    #         column_id = 'your_icebox_column_id'
    #     # Add more conditions as necessary
        
    #     # Print pipeline all fields
    #     print(pipeline)

    #     # if column_id:
    #     #     for issue in pipeline['issues']:
    #     #         issue_title = issue['issue_title']
    #     #         issue_body = f"ZenHub Issue ID: {issue['issue_number']}"
    #     #         labels = [pipeline['name']]
    #     #         github_issue = create_github_issue(issue_title, issue_body, labels)
    #     #         add_issue_to_project(github_issue['id'], column_id)


if __name__ == "__main__":
    sync_tickets()
