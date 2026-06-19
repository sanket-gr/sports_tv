import pytest
from scrapers import extract_async

@pytest.mark.asyncio
async def test_extract_invalid_url():
    result = await extract_async("https://example.com")
    assert isinstance(result, dict)
    assert result["title"].startswith("[ERROR]")

@pytest.mark.asyncio
async def test_extract_embed_st_routing():
    result = await extract_async("https://embed.st/embed/admin/dummy/1")
    assert isinstance(result, dict)

