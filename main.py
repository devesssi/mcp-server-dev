"""
MCP Server: Fetch Hugging Face Blogs
"""

from mcp.server.fastmcp import FastMCP
import requests
from bs4 import BeautifulSoup
import logging

mcp = FastMCP(
    "huggingface-blogs",
    dependencies=["requests", "beautifulsoup4"]
)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/115.0 Safari/537.36"
    )
}

@mcp.tool()
def fetch_huggingface_blogs(topic: str = "") -> list:
    """
    Fetch recent Hugging Face blog posts. Optionally filter by topic.
    Returns up to 5 posts with title, url, and description.
    """
    url = "https://huggingface.co/blog"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        logging.error(f"Failed to fetch Hugging Face blog: {e}")
        return []

    posts = parse_blog_page(response.text)

    # Filter if topic provided
    if topic.strip():
        topic_lower = topic.lower()
        posts = [
            p for p in posts
            if topic_lower in p["title"].lower() or
               topic_lower in p.get("description", "").lower()
        ]

    return posts[:5]


def parse_blog_page(html_text: str) -> list:
    """
    Parse Hugging Face blog HTML and extract titles, URLs, and descriptions.
    """
    soup = BeautifulSoup(html_text, "html.parser")
    posts = []

    # Each blog entry is usually inside <article>
    for article in soup.select("article a[href^='/blog/']"):
        link = article.get("href")
        if not link or "?tag=" in link:  # 🚫 skip tag/category links
            continue

        # Extract title
        title = None
        if article.find("h3"):
            title = article.find("h3").get_text(strip=True)
        elif article.get("title"):
            title = article["title"]
        else:
            title = article.get_text(strip=True)

        if not title or len(title) < 5:
            continue

        full_url = f"https://huggingface.co{link}" if link.startswith("/") else link

        # Try to extract short description (from sibling <p>)
        description = ""
        parent_article = article.find_parent("article")
        if parent_article:
            desc_tag = parent_article.find("p")
            if desc_tag:
                description = desc_tag.get_text(strip=True)

        posts.append({
            "title": title,
            "url": full_url,
            "description": description
        })

    # Deduplicate by URL
    seen, unique_posts = set(), []
    for p in posts:
        if p["url"] not in seen:
            unique_posts.append(p)
            seen.add(p["url"])

    return unique_posts



@mcp.resource("greeting://{name}")
def get_greeting(name: str) -> str:
    """Get a personalized greeting."""
    return f"Hello, {name}!"



@mcp.prompt()
def greet_user(name: str, style: str = "friendly") -> str:
    """Generate a greeting prompt."""
    styles = {
        "friendly": "Please write a warm, friendly ",
        "formal": "Please write a formal, professional greeting",
        "casual": "Please write a casual, relaxed greeting",
    }

    return f"{styles.get(style, styles['friendly'])} for someone named {name}."
