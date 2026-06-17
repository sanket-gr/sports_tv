from abc import ABC, abstractmethod
from typing import Any, Dict, Union, List

class BaseScraper(ABC):
    """
    Abstract base class for all stream scrapers.
    """
    
    @abstractmethod
    async def extract(self, url: str, browser: Any = None) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """
        Extract stream metadata and HLS URL from the given source URL.
        Returns a dictionary or a list of dictionaries (if multiple servers exist).
        """
        pass
