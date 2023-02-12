import base64
import json
import requests

# Open the "environments.json" file and read its contents into the "environments" dictionary
with open("environments.json", encoding="utf-8") as f:
    environments = json.load(f)

# Open the "secrets.json" file and read its contents into the "secrets" dictionary
with open("secrets.json", encoding="utf-8") as f:
    secrets = json.load(f)
    # Unpack the "secrets" dictionary
    organisation = secrets["organisation"]
    username = secrets["username"]
    pat_token = secrets["pat_token"]


def get_file_contents(project, repository, file_path):
    """
    Get the contents of a file from the Azure DevOps repository.

    :param project: the name of the Azure DevOps project
    :param repository: the name of the repository in the Azure DevOps project
    :param file_path: the path of the file in the repository
    :return: the contents of the file as a string
    :raise FileNotFoundError: if the file could not be retrieved,
      an exception is raised with a message indicating the reason for failure
    """
    # Construct the URL for the Azure DevOps API request
    url = (
        "https://dev.azure.com/"
        + f"{organisation}/{project}"
        + f"/_apis/git/repositories/{repository}/items?path={file_path}"
    )
    # Encode the username and PAT token for Basic Authentication
    auth = base64.b64encode(f"{username}:{pat_token}".encode()).decode()
    # Send the API request to retrieve the file contents
    try:
        response = requests.get(
            url,
            headers={"Authorization": f"Basic {auth}", "Cache-Control": "no-cache"},
            timeout=10,
        )
    except requests.exceptions.RequestException as exception:
        raise FileNotFoundError(
            f"Failed to retrieve {file_path} file. Reason: {str(exception)}"
        ) from exception

    # Check the response status code
    if response.status_code == 200:
        # If the request was successful, return the file contents
        content = response.text
        return content
    # If the request was unsuccessful, raise an exception
    raise FileNotFoundError(
        f"Failed to retrieve {file_path} file. Response: {response.content}"
    )


def get_version(software, file_contents):
    """
    Get the version of the specified software from the contents of a file.

    :param software: The name of the software to get the version for.
    Must be either 'ansible' or 'terraform'.
    :param file_contents: The contents of the file to extract the version from.
    :return: The version of the specified software.
    :raises: ValueError if the specified software is unknown.
    :raises: LookupError if the version of the specified software
    could not be found in the file contents.
    """
    # Split the contents of the file into lines
    lines = file_contents.splitlines()

    # Check the type of software
    if software == "ansible":
        # Use a list comprehension to extract the version of Ansible
        temp_version = [
            line.split("==")[1] for line in lines if line.startswith("ansible")
        ]

        # If the version was found, return it
        if temp_version:
            return temp_version[0]

        # If the version was not found, raise an exception
        raise LookupError("Ansible version not found in the file.")

    elif software == "terraform":
        # Use a list comprehension to extract the version of Terraform
        temp_version = [
            line.split(": '")[1].strip("'")
            for line in lines
            if "terraformVersion: '" in line
        ]

        # If the version was found, return it
        if temp_version:
            return temp_version[0]

        # If the version was not found, raise an exception
        raise LookupError("Terraform version not found in the file.")

    # If the software type is unknown, raise an exception
    else:
        raise ValueError(f"Unknown software: {software}")


def save_to_json(content, file_name):
    """
    Saves the given content to a JSON file with the specified name.

    :param content: The data to be saved in the JSON file.
    :param file_name: The name of the file to save the JSON data to.
    """
    with open(file_name, "w", encoding="utf-8") as w:
        json.dump(content, w, ensure_ascii=False, indent=4)


if __name__ == "__main__":
    # Initialize the data list
    data = []

    for env in environments:
        if "file_path" not in env:
            data.append(
                {
                    "dependency": env["software"],
                    "version": env["version"],
                    "env": env["envName"],
                    "repo": env["repo"],
                }
            )
            continue

        # Get the requirements.txt file
        file_content = get_file_contents(env["project"], env["repo"], env["file_path"])

        # Get the version of Ansible
        version = get_version(env["software"], file_content)

        # Add the Ansible version and env to the data list
        data.append(
            {
                "dependency": env["software"],
                "version": version,
                "env": env["envName"],
                "repo": env["repo"],
                "project": env["project"],
            }
        )

    # Save the data to a JSON file
    save_to_json(data, "versions.json")
