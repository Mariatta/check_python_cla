from check_python_cla.github import (
    SEARCH_PR_URL,
    get_and_update_pending_prs,
    get_user_pending_pull_requests,
    update_pr_cla_status,
)


class FakeGH:
    def __init__(self, *, getitem=None):
        self._getitem_return = getitem
        self.getitem_url = None

    async def getitem(self, url, *, accept=None):
        self.getitem_url = url
        to_return = self._getitem_return[self.getitem_url]
        return to_return

    async def patch(self, url, *, data):
        self.patch_url = url
        self.patch_data = data


async def test_get_pending_prs_for_user_no_items():
    username = "miss-islington"
    getitem = {
        SEARCH_PR_URL.format(gh_username=username): {"total_count": 0, "items": []}
    }
    gh = FakeGH(getitem=getitem)
    result = await get_user_pending_pull_requests(gh, username)
    assert result == []


async def test_get_pending_prs_for_user_with_items():
    username = "miss-islington"
    getitem = {
        SEARCH_PR_URL.format(gh_username=username): {
            "total_count": 1,
            "items": [
                {
                    "url": "https://api.github.com/repos/python/cpython/issues/8456",
                    "number": 8456,
                    "title": "Update Windows install path to Python 3.7",
                    "labels": [
                        {"name": "CLA not signed"},
                        {"name": "awaiting review"},
                        {"name": "type-documentation"},
                    ],
                }
            ],
        }
    }
    gh = FakeGH(getitem=getitem)
    result = await get_user_pending_pull_requests(gh, username)
    assert result == [
        {
            "url": "https://api.github.com/repos/python/cpython/issues/8456",
            "number": 8456,
            "title": "Update Windows install path to Python 3.7",
            "labels": [
                {"name": "CLA not signed"},
                {"name": "awaiting review"},
                {"name": "type-documentation"},
            ],
        }
    ]


async def test_update_pr_cla_status():
    pr_data = {
        "url": "https://api.github.com/repos/python/cpython/issues/8456",
        "number": 8456,
        "title": "Update Windows install path to Python 3.7",
        "labels": [
            {"name": "CLA not signed"},
            {"name": "awaiting review"},
            {"name": "type-documentation"},
        ],
    }
    gh = FakeGH()
    await update_pr_cla_status(gh, pr_data)
    assert gh.patch_url == "https://api.github.com/repos/python/cpython/issues/8456"
    assert gh.patch_data == {"labels": ["awaiting review", "type-documentation"]}


async def test_get_and_update_pending_prs():
    username = "miss-islington"
    getitem = {
        SEARCH_PR_URL.format(gh_username=username): {
            "total_count": 1,
            "items": [
                {
                    "url": "https://api.github.com/repos/python/cpython/issues/8456",
                    "number": 8456,
                    "title": "Update Windows install path to Python 3.7",
                    "labels": [
                        {"name": "CLA not signed"},
                        {"name": "awaiting review"},
                        {"name": "type-documentation"},
                    ],
                }
            ],
        }
    }
    gh = FakeGH(getitem=getitem)
    result = await get_and_update_pending_prs(gh, username)
    assert gh.patch_url == "https://api.github.com/repos/python/cpython/issues/8456"
    assert gh.patch_data == {"labels": ["awaiting review", "type-documentation"]}
    assert result == [
        {
            "url": "https://api.github.com/repos/python/cpython/issues/8456",
            "number": 8456,
            "title": "Update Windows install path to Python 3.7",
            "labels": [
                {"name": "CLA not signed"},
                {"name": "awaiting review"},
                {"name": "type-documentation"},
            ],
        }
    ]
