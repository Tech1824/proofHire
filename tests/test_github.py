import pytest
from ingest.github import parse_github_username as parse_username, fetch_github_profile

def test_parse_username():
    assert parse_username("https://github.com/pro-npc") == "pro-npc"
    assert parse_username("https://github.com/pro-npc/") == "pro-npc"
    assert parse_username("https://github.com/pro-npc?tab=repositories") == "pro-npc"
    assert parse_username("invalid_url") is None

def test_fetch_real_user():
    result = fetch_github_profile("https://github.com/octocat")
    assert "projects" in result
    assert "warnings" in result
    
    # Octocat should have repos
    if not result["warnings"] or "rate limit" not in result["warnings"][0].lower():
        assert len(result["projects"]) > 0

def test_fetch_nonexistent_user():
    result = fetch_github_profile("https://github.com/thisuserdoesnotexist123456789")
    assert "projects" in result
    assert "warnings" in result
    assert result["projects"] == []
    assert "not found" in result["warnings"][0].lower() or "rate limit" in result["warnings"][0].lower()
