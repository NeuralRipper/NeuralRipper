import httpx
from fastapi import APIRouter, HTTPException

from settings import GITHUB_API_KEY

router = APIRouter(prefix="/github")

CONTRIBUTIONS_QUERY = """
query($username: String!) {
    user(login: $username) {
        contributionsCollection {
            contributionCalendar {
                totalContributions
                weeks {
                    contributionDays {
                        contributionCount
                        date
                    }
                }
            }
        }
    }
}
"""


@router.get("/contributions")
async def get_contributions():
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "https://api.github.com/graphql",
            headers={"Authorization": f"Bearer {GITHUB_API_KEY}"},
            json={"query": CONTRIBUTIONS_QUERY, "variables": {"username": "dizzydoze"}},
        )
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail="GitHub API error")
    return resp.json()
