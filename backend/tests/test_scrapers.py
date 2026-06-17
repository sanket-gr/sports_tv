import pytest
from scrapers import extract_async

@pytest.mark.asyncio
async def test_extract_invalid_url():
    result = await extract_async("https://example.com")
    assert isinstance(result, dict)
    assert result["title"].startswith("[ERROR]")
