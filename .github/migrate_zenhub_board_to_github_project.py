import requests
import os
import jq

GITHUB_ORG = "dereksu-org"
GITHUB_REPO = "gha-playground"
GITHUB_PROJECT = "helloworld"
GITHUB_API_URL = "https://api.github.com"
GITHUB_GRAPHQL_URL = "https://api.github.com/graphql"


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


def get_zenhub_board():
    url = ZENHUB_API_URL.format(repo_id=get_github_repo_id())
    headers = {
        "Content-Type": "application/json",
        "X-Authentication-Token": ZENHUB_ACCESS_TOKEN
    }

    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        response.raise_for_status()


def get_github_project_node_id():
    query = '''
    {
      repository(owner: "%s", name: "%s") {
        projectsV2(first: 100) {
          nodes {
            id
            title
          }
        }
      }
    }
    ''' % (GITHUB_ORG, GITHUB_REPO)

    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Content-Type": "application/json"
    }
    data = {
        "query": query
    }

    response = requests.post(GITHUB_GRAPHQL_URL, json=data, headers=headers)
    if response.status_code == 200:
        result = response.json()
        project_id = jq.first(f'.data.repository.projectsV2.nodes[] | select(.title == "{GITHUB_PROJECT}") | .id', result)
        return project_id
    else:
        raise Exception(f"Query failed to run by returning code of {response.status_code}. {response.text}")


def get_github_issue(issue_number):
    url = f"https://api.github.com/repos/{GITHUB_ORG}/{GITHUB_REPO}/issues/{issue_number}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }

    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        response.raise_for_status()


def get_github_project_statuses(project_number):
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Content-Type": "application/json"
    }
    query = '''
    query {
      repository(owner: "%s", name: "%s") {
        projectV2(number: %d) {
          id
          title
          fields(first: 10) {
            nodes {
              ... on ProjectV2FieldCommon {
                id
                name
              }
              ... on ProjectV2SingleSelectField {
                id
                name
                options {
                  id
                  name
                }
              }
            }
          }
        }
      }
    }
    ''' % (GITHUB_ORG, GITHUB_REPO, project_number)
    payload = {
        "query": query
    }

    response = requests.post(GITHUB_GRAPHQL_URL, headers=headers, json=payload)
    if response.status_code == 200:
        nodes = response.json().get("data").get("repository").get("projectV2").get("fields").get("nodes")
        for node in nodes:
            if node.get("name") == "Status":
                # Convert node.get("options") to a dictionary
                return node.get("id"), {option.get("name"): option.get("id") for option in node.get("options")}
    else:
        response.raise_for_status()


def get_github_project():
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Content-Type": "application/json"
    }
    query = '''
    {
      organization(login: "%s") {
        projectsV2(first: 20) {
          nodes {
            id
            title
            number
          }
        }
      }
    }
    ''' % (GITHUB_ORG)
    payload = {
        "query": query
    }

    response = requests.post(GITHUB_GRAPHQL_URL, headers=headers, json=payload)
    if response.status_code == 200:
        return response.json().get("data").get("organization").get("projectsV2").get("nodes")[0]
    else:
        response.raise_for_status()


def add_project_item(token, project_id, content_id):
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Content-Type": "application/json"
    }
    query = '''
    mutation {
      addProjectV2ItemById(input: {projectId: "%s", contentId: "%s"}) {
        item {
          id
        }
      }
    }
    ''' % (project_id, content_id)
    payload = {
        "query": query
    }

    response = requests.post(GITHUB_GRAPHQL_URL, headers=headers, json=payload)
    return response.json()


def migrate_tickets():
    # Get status map from GitHub project
    project = get_github_project()
    project_number = project.get("number")
    project_id = project.get("id")

    node_id, statuses = get_github_project_statuses(project_number)
    print(node_id)
    print(statuses)

    board = get_zenhub_board()
    for pipeline in board['pipelines']:
        column_name = pipeline['name']

        print(column_name)
        # Iterating through each ticket in the pipeline,
        # and creating a corresponding GitHub issue
        for issue in pipeline['issues']:
            issue = get_github_issue(issue['issue_number'])
            issue_id = issue['node_id']

            add_project_item(project_id, issue_id)
            # issue_title = issue['issue_title']
            # issue_body = f"ZenHub Issue ID: {issue['issue_number']}"
            # labels = [pipeline['name']]
            # github_issue = create_github_issue(issue_title, issue_body, labels)
            # add_issue_to_project(github_issue['id'], column_id)

    node_id = get_github_project_node_id()
    print(node_id)
    #     # if column_id:
    #     #     for issue in pipeline['issues']:
    #     #         issue_title = issue['issue_title']
    #     #         issue_body = f"ZenHub Issue ID: {issue['issue_number']}"
    #     #         labels = [pipeline['name']]
    #     #         github_issue = create_github_issue(issue_title, issue_body, labels)
    #     #         add_issue_to_project(github_issue['id'], column_id)


if __name__ == "__main__":
    migrate_tickets()
