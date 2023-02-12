import datetime
import json
from packaging.version import Version
import requests


def get_eol_date(dependency: str, release_cycle: str):
    """Get the end of life date for a specific version of a dependency.

    Args:
        dependency (str): The name of the dependency.
        release_cycle (str): The version of the dependency.

    Returns:
        datetime.date: The end of life date for the dependency and version.
        None: If the API request fails or the response is not 200 OK.
    """
    url = f"https://endoflife.date/api/{dependency}/{release_cycle}.json"
    response = requests.get(url, timeout=10)
    if response.status_code == 200:
        data = response.json()
        eol = datetime.datetime.strptime(data["eol"], "%Y-%m-%d").date()
        return eol
    return None


def get_latest_version(dependency: str):
    """Get the latest version of a dependency.

    Args:
        dependency (str): The name of the dependency.

    Returns:
        str: The latest version of the dependency.
        None: If the API request fails or the response is not 200 OK.
    """
    product_url = f"https://endoflife.date/api/{dependency}.json"
    response = requests.get(product_url, timeout=10)
    if response.status_code == 200:
        product_data = response.json()
        latest_version = sorted(
            product_data, key=lambda x: Version(x["cycle"]), reverse=True
        )[0]["latest"]
        return latest_version
    return None


def check_support_status(dependency: str, version: str, env: str, repo: str):
    """Check the support status of a specific version of a dependency.

    Args:
        dependency (str): The name of the dependency.
        version (str): The version of the dependency.
        env (str): The environment the dependency is running in.
        repo (str): The repository where the dependency is stored.

    Returns:
        tuple: A tuple containing the following elements:
            - dependency (str): The name of the dependency.
            - version (str): The version of the dependency.
            - eol (datetime.date): The end of life date for the dependency and version.
            - env (str): The environment the dependency is running in.
            - repo (str): The repository where the dependency is stored.
            - latest (str): The latest version of the dependency.
        None: If the end of life date could not be retrieved.
    """
    eol = get_eol_date(dependency, version)
    if not eol:
        if "." in version:
            return check_support_status(
                dependency, ".".join(version.rsplit(".", 1)[:-1]), env, repo
            )
        return None
    latest = get_latest_version(dependency)
    return (dependency, version, eol, env, repo, latest)


def log_support_status_old(eols):
    """Log the support status of a list of dependencies and their versions.

    Args:
        eols (list of tuples): A list of tuples, each containing the following elements:
            - dependency (str): The name of the dependency.
            - version (str): The version of the dependency.
            - eol (datetime.date): The end of life date for the dependency and version.
            - env (str): The environment the dependency is running in.
            - repo (str): The repository where the dependency is stored.
            - latest (str): The latest version of the dependency.

    Returns:
        None
    """
    today = datetime.date.today()
    for dependency, version, eol, env, repo, latest in eols:
        if eol >= today:
            print(
                f"{dependency} version {version} in the {env} environment"
                + f" will reach end of life on {eol}."
                + f" Check repo: {repo}. Latest version: {latest}"
            )
        else:
            print(
                f"{dependency} version {version} in the {env} environment"
                + f" ran out of support on {eol}."
                + f" Check repo: {repo}. Latest version: {latest}"
            )


def log_support_status(eols):
    """Log the support status of a list of dependencies and their versions.

    Args:
        eols (list of tuples): A list of tuples, each containing the following elements:
            - dependency (str): The name of the dependency.
            - version (str): The version of the dependency.
            - eol (datetime.date): The end of life date for the dependency and version.
            - env (str): The environment the dependency is running in.
            - repo (str): The repository where the dependency is stored.
            - latest (str): The latest version of the dependency.

    Returns:
        None
    """
    today = datetime.date.today()
    eols_dict = {}
    for dependency, version, eol, env, repo, latest in eols:
        if (dependency, version) in eols_dict:
            eols_dict[(dependency, version)]["env"].append(env)
            eols_dict[(dependency, version)]["repo"].append(repo)
        else:
            eols_dict[(dependency, version)] = {
                "eol": eol,
                "env": [env],
                "repo": [repo],
                "latest": latest,
            }

    for (dependency, version), info in eols_dict.items():
        if info["eol"] >= today:
            print(
                f"{dependency} version {version} in the {', '.join(info['env'])} environment(s)"
                + f" will reach end of life on {info['eol']}."
                + f" Check repo(s): {', '.join(info['repo'])}. Latest version: {info['latest']}"
            )
        else:
            print(
                f"{dependency} version {version} in the {', '.join(info['env'])} environment(s)"
                + f" ran out of support on {info['eol']}."
                + f" Check repo(s): {', '.join(info['repo'])}. Latest version: {info['latest']}"
            )


def main():
    """The main function that reads the dependencies from a JSON file
    and checks their support status."""
    with open("versions.json", encoding="UTF-8") as f:
        dependencies = json.load(f)

    print(f"Checking {len(dependencies)} software versions")

    eols = [
        check_support_status(dep["dependency"], dep["version"], dep["env"], dep["repo"])
        for dep in dependencies
    ]
    eols = [eol for eol in eols if eol is not None]

    eols.sort(key=lambda x: x[2])

    log_support_status(eols)


if __name__ == "__main__":
    main()
