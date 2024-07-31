import requests
import os
import jq

GITHUB_ORG = "dereksu-org"
GITHUB_REPO = "gha-playground"
GITHUB_PROJECT = "helloworld"
GITHUB_API_URL = "https://api.github.com"
GITHUB_GRAPHQL_URL = "https://api.github.com/graphql"

ZENHUB_API_URL = "https://api.zenhub.com/p1/repositories/{repo_id}/board"

def get_github_repo_id(github_token):
    url = f"{GITHUB_API_URL}/repos/{GITHUB_ORG}/{GITHUB_REPO}"
    headers = {
        "Authorization": github_token
    }

    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        print("Debug ==>", response.json().get("id"))
        return response.json().get("id")
    else:
        response.raise_for_status()


def get_zenhub_board(zenhub_token, github_token):
    url = ZENHUB_API_URL.format(repo_id=get_github_repo_id(github_token))
    headers = {
        "Content-Type": "application/json",
        "X-Authentication-Token": zenhub_token
    }

    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        response.raise_for_status()


def get_github_issue(github_token, github_org, github_repo, issue_number):
    url = f"https://api.github.com/repos/{github_org}/{github_repo}/issues/{issue_number}"
    headers = {
        "Authorization": f"token {github_token}",
        "Accept": "application/vnd.github.v3+json"
    }

    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        response.raise_for_status()


def get_github_project_status(github_token, project_number):
    headers = {
        "Authorization": f"Bearer {github_token}",
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


def get_github_project(github_token, github_org, github_project):
    headers = {
        "Authorization": f"Bearer {github_token}",
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
    ''' % (github_org)
    payload = {
        "query": query
    }

    response = requests.post(GITHUB_GRAPHQL_URL, headers=headers, json=payload)
    if response.status_code == 200:
        # fine project by title
        for project in response.json().get("data").get("organization").get("projectsV2").get("nodes"):
            if project.get("title") == github_project:
                return project
    else:
        response.raise_for_status()


def add_github_project_item(github_token, project_id, content_id):
    headers = {
        "Authorization": f"Bearer {github_token}",
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


def move_item_to_status(github_token, project_id, item_id, field_id, single_select_option_id):
    headers = {
        "Authorization": f"Bearer {github_token}",
        "Content-Type": "application/json"
    }
    query = '''
    mutation {
      updateProjectV2ItemFieldValue(input: {projectId: "%s", itemId: "%s", fieldId: "%s", value: {singleSelectOptionId: "%s"}}) {
        projectV2Item {
          id
        }
      }
    }
    ''' % (project_id, item_id, field_id, single_select_option_id)
    payload = {
        "query": query
    }

    response = requests.post(GITHUB_GRAPHQL_URL, headers=headers, json=payload)
    if response.status_code == 200:
        return response.json()
    else:
        response.raise_for_status()


def migrate_tickets():
    github_token = os.getenv("GITHUB_TOKEN")
    zenhub_token = os.getenv("ZENHUB_ACCESS_TOKEN")
    github_org = os.getenv("GITHUB_ORG")
    github_repo = os.getenv("GITHUB_REPO")
    github_project = os.getenv("GITHUB_PROJECT")
    

    # Get the GitHub Project details
    project = get_github_project(github_token, github_org)
    print(f"GitHub Project Details: {project}")
    project_number = project.get("number")
    project_id = project.get("id")
    node_id, status = get_github_project_status(github_token, project_number)
    print(f"GitHub Project Details: number={project_number}, id={project_id}, status={status}")

    # Get the ZenHub board details
    board = get_zenhub_board(zenhub_token, github_token)
    for pipeline in board['pipelines']:
        # Iterating through each pipeline, which are corresponding to the GitHub Project statuses (columns)
        column_name = pipeline['name']

        print(column_name)
        # Iterating through each ticket in the pipeline,
        # and creating a corresponding GitHub issue
        for issue in pipeline['issues']:
            issue = get_github_issue(github_token, github_org, github_repo,
                                     issue['issue_number'])

            result = add_github_project_item(github_token,
                                             project_id, issue['node_id'])
            item_id = result['data']['addProjectV2ItemById']['item']['id']
            move_item_to_status(github_token,
                                project_id, item_id, node_id,
                                status[column_name])


if __name__ == "__main__":
    migrate_tickets()
