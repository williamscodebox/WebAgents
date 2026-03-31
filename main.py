import asyncio
import json
import os
import nest_asyncio
import pprint
import base64
from io import BytesIO
import pandas as pd
from playwright.async_api import async_playwright
from openai import OpenAI
from PIL import Image
from tabulate import tabulate
from IPython.display import display, HTML, Markdown
from pydantic import BaseModel
from helper import get_openai_api_key, visualizeCourses, get_local_client
from openai.types.chat import (
    ChatCompletionSystemMessageParam,
    ChatCompletionUserMessageParam
)
from bs4 import BeautifulSoup
import webbrowser


# ---------------------------
# LM Studio LLM CONFIG
# ---------------------------

lmstudio_llm_config = {
    "config_list": [
        {
            "model": "local-lmstudio",              # arbitrary name
            "api_key": "lm-studio",                # ignored by LM Studio, required by AutoGen
            "base_url": "http://localhost:1234/v1",
            "price": [0,0] # to silence model warning
        }
    ],
    "temperature": 0.7,
}


# client = OpenAI(api_key=get_openai_api_key()) # use this one for running openAI on the cloud
client = OpenAI(
    api_key="lm-studio",
    base_url="http://localhost:1234/v1"
)


nest_asyncio.apply()



class WebScraperAgent:
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.page = None

    async def init_browser(self):
      self.playwright = await async_playwright().start()
      self.browser = await self.playwright.chromium.launch(
          headless=True,
          args=[
              "--disable-dev-shm-usage",
              "--no-sandbox",
              "--disable-setuid-sandbox",
              "--disable-accelerated-2d-canvas",
              "--disable-gpu",
              "--no-zygote",
              "--disable-audio-output",
              "--disable-software-rasterizer",
              "--disable-webgl",
              "--disable-web-security",
              "--disable-features=LazyFrameLoading",
              "--disable-features=IsolateOrigins",
              "--disable-background-networking"
          ]
      )
      self.page = await self.browser.new_page()

    async def scrape_content(self, url):
        if not self.page or self.page.is_closed():
            await self.init_browser()
        await self.page.goto(url, wait_until="load")
        await self.page.wait_for_timeout(2000)  # Wait for dynamic content
        return await self.page.content()

    async def take_screenshot(self, path="screenshot.png"):
        await self.page.screenshot(path=path, full_page=True)
        return path
    async def screenshot_buffer(self):
        screenshot_bytes = await self.page.screenshot(type="png", full_page=False)
        return screenshot_bytes

    async def close(self):
        if self.page and not self.page.is_closed():
            await self.page.close()

        if self.browser:
            await self.browser.close()

        if self.playwright:
            await self.playwright.stop()

        self.playwright = None
        self.browser = None
        self.page = None


scraper = WebScraperAgent()

class DeeplearningCourse(BaseModel):
    title: str
    description: str
    presenter: list[str]
    imageUrl: str
    courseURL: str

class DeeplearningCourseList(BaseModel):
    courses: list[DeeplearningCourse]

async def process_with_llm(html, instructions, truncate=False):
    completion = client.beta.chat.completions.parse(
        model="gpt-4o-mini-2024-07-18",
        messages=[
            ChatCompletionSystemMessageParam(
                role="system",
                content=f"""
                You are an expert web scraping agent. Your task is to extract structured
                course information from the provided HTML. Follow these instructions:

                {instructions}

                Return ONLY valid JSON matching the DeeplearningCourseList schema.
                                """
            ),
            ChatCompletionUserMessageParam(
                role="user",
                content=html[:150000]
            )
        ],
        temperature=0.1,
        response_format=DeeplearningCourseList,
    )
    return completion.choices[0].message.parsed

def clean_html(html):
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "meta", "noscript"]):
        tag.decompose()
    text = soup.get_text(separator=" ", strip=True)
    return text



async def webscraper(target_url, instructions):
    result = None
    try:
        # Scrape content and capture screenshot
        print("Extracting HTML Content \n")
        html_content = await scraper.scrape_content(target_url)

        # CLEAN + TRUNCATE HTML HERE
        html_content = clean_html(html_content)[:20000]

        print("Taking Screenshot \n")
        screenshot = await scraper.screenshot_buffer()
        # Process content

        print("Processing..")
        result: DeeplearningCourseList = await process_with_llm(html_content, instructions, False)
        print("\nGenerated Structured Response")
    except Exception as e:
        print(f"❌ Error: {str(e)}")
    finally:
        await scraper.close()
    return result, screenshot

async def main():
    target_url = "https://www.deeplearning.ai/courses"
    base_url = "https://deeplearning.ai"

    instructions = """
        Get all the courses
    """

    result, screenshot = await webscraper(target_url, instructions)

    html = await visualizeCourses(
        result=result,
        screenshot=screenshot,
        target_url=target_url,
        instructions=instructions,
        base_url=base_url
    )

    with open("output.html", "w", encoding="utf-8") as f:
        f.write(html)

    print("Visualization saved to output.html")

    output_path = os.path.abspath("output.html")
    webbrowser.open(f"file://{output_path}")


if __name__ == "__main__":
    asyncio.run(main())
