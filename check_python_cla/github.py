SEARCH_PR_URL = '/search/issues?q=type:pr+author:{gh_username}+state:open+org:python+label:"CLA not signed"&sort=created&order=asc'


async def get_user_pending_pull_requests(gh, gh_username):
    """Retrieve open prs for the GitHub user where there is `CLA not signed` label."""
    result = await gh.getitem(
        SEARCH_PR_URL.format(gh_username=gh_username),
        accept="application/vnd.github.symmetra-preview+json",
    )
    return result["items"]


async def update_pr_cla_status(gh, pr_data):
    """Remove the `CLA not signed` label from the PR."""
    pr_labels = [
        label["name"]
        for label in pr_data["labels"]
        if label["name"] != "CLA not signed"
    ]
    await gh.patch(pr_data["url"], data={"labels": pr_labels})


async def get_and_update_pending_prs(gh, gh_username):
    """Retrieve open PRs, and remove the `CLA not signed` label from the PRs."""
    pending_prs = await get_user_pending_pull_requests(gh, gh_username)

    for pending_pr in pending_prs:
        await update_pr_cla_status(gh, pending_pr)

    if len(pending_prs) > 0:
        return pending_prs
    else:
        return []
