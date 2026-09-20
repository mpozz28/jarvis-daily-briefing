import json
import logging
import os
import tarfile
import tempfile

import requests
from bs4 import BeautifulSoup

from src.config import DATA_DIR

logger = logging.getLogger(__name__)
CACHE_DIR = os.path.join(DATA_DIR, "source_cache")
os.makedirs(CACHE_DIR, exist_ok=True)


class SourceCache:
    def __init__(self):
        self.cache_dir = CACHE_DIR

    def _get_cache_path(self, item_id: str) -> str:
        safe_name = "".join(c if c.isalnum() else "_" for c in item_id)
        return os.path.join(self.cache_dir, f"{safe_name}.json")

    def fetch_and_cache(self, item: dict) -> str:
        """Downloads the full text and saves it to the cache."""
        item_id = item.get("id", "")
        url = item.get("url", item_id)
        cache_path = self._get_cache_path(item_id)

        if os.path.exists(cache_path):
            try:
                with open(cache_path, "r", encoding="utf-8") as f:
                    return json.load(f).get("content", "")
            except Exception as e:
                logger.warning(f"Cache read error for {item_id}: {e}")

        content = ""
        logger.info(f"Downloading source for: {item.get('title', '')[:30]}...")

        try:
            if "arxiv.org" in url:
                content = self._fetch_arxiv_latex(url)
                if not content:
                    content = item.get("description", "") + "\n[LaTeX TEXT UNAVAILABLE]"
            else:
                content = self._fetch_web_text(url)
                if not content:
                    content = item.get("description", "")
        except Exception as e:
            logger.error(f"Download error {url}: {e}")
            content = item.get("description", "")

        try:
            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump(
                    {"id": item_id, "title": item.get("title"), "content": content}, f
                )
        except Exception as e:
            logger.error(f"Unable to save cache: {e}")

        return content

    def _fetch_arxiv_latex(self, url: str) -> str:
        """Extracts the raw LaTeX source code from ArXiv."""
        eprint_url = url.replace("/abs/", "/e-print/")
        try:
            response = requests.get(eprint_url, stream=True, timeout=15)
            if response.status_code != 200:
                return ""

            tex_content = ""
            with tempfile.NamedTemporaryFile(delete=False) as tmp:
                for chunk in response.iter_content(chunk_size=8192):
                    tmp.write(chunk)
                tmp_path = tmp.name

            with tarfile.open(tmp_path, "r:gz") as tar:
                for member in tar.getmembers():
                    if member.name.endswith(".tex"):
                        f = tar.extractfile(member)
                        if f:
                            tex_content += (
                                f.read().decode("utf-8", errors="ignore") + "\n\n"
                            )

            os.remove(tmp_path)
            return tex_content
        except Exception as e:
            logger.warning(f"Failed to download LaTeX from ArXiv: {e}")
            return ""

    def _fetch_web_text(self, url: str) -> str:
        """Extracts ONLY the relevant text from the webpage, ignoring menus/ads."""
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code != 200:
                return ""

            soup = BeautifulSoup(response.text, "html.parser")

            # Target the article tag (used by 90% of news publishers)
            article = soup.find("article")
            if article:
                return article.get_text(separator=" ", strip=True)

            # Fallback: extract only paragraphs
            paragraphs = soup.find_all("p")
            text = " ".join([p.get_text(strip=True) for p in paragraphs])
            return text if text else soup.get_text(separator=" ", strip=True)
        except Exception:
            return ""


source_cache = SourceCache()
