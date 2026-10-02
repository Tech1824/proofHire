from ingest.github import fetch_github_profile, parse_github_username

def test_parse():
    assert parse_github_username("https://github.com/pro-npc") == "pro-npc"
    assert parse_github_username("github.com/pro-npc/") == "pro-npc"
    assert parse_github_username("https://github.com/pro-npc/tab/repos") == "pro-npc"
    print("parse_github_username tests passed")

def test_fetch_real():
    print("\nFetching real user (pro-npc)...")
    res = fetch_github_profile("https://github.com/pro-npc")
    print(f"Warnings: {res.get('warnings')}")
    print(f"Projects found: {len(res.get('projects'))}")
    if res.get('projects'):
        proj = res['projects'][0]
        print(f"Top project: {proj['name']} - Files: {len(proj['files'])}")

def test_fetch_fake():
    print("\nFetching fake user (this-user-does-not-exist-123456789)...")
    res = fetch_github_profile("https://github.com/this-user-does-not-exist-123456789")
    print(f"Warnings: {res.get('warnings')}")

if __name__ == "__main__":
    test_parse()
    test_fetch_real()
    test_fetch_fake()
