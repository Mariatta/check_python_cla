import enum
import json

from check_python_cla.exceptions import CheckCLAException

BPO_URL = "https://bugs.python.org/user?@template=clacheck&github_names="


class Status(enum.Enum):
    """The CLA status of the contribution."""

    signed = 1
    not_signed = 2
    username_not_found = 3


async def check_cla(session, gh_username):
    """Check in bpo if user has signed the CLA."""
    async with session.get(f"{BPO_URL}{gh_username}") as response:
        if response.status >= 300:

            msg = f"unexpected response for {response.url!r}: {response.status}"
            raise CheckCLAException(msg)
            # Explicitly decode JSON as b.p.o doesn't set the content-type as
            # `application/json`.
        results = json.loads(await response.text())
        try:
            status = results[gh_username]
        except KeyError:
            raise CheckCLAException(f"Invalid input: {gh_username}")
        else:
            if status is True:
                return Status.signed.value
            elif status is False:
                return Status.not_signed.value
            else:
                return Status.username_not_found.value
