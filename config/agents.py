import os
from textwrap import dedent

from crewai import Agent
from crewai_tools import ScrapeWebsiteTool, SerperDevTool
from dotenv import load_dotenv
from langchain_mistralai import ChatMistralAI
from langchain_openai import ChatOpenAI

from tools import scrape_linkedin_posts_tool

load_dotenv()


openai_llm = ChatOpenAI(api_key=os.environ.get("OPENAI_API_KEY"), model="gpt-4.1")
mistral_llm = ChatMistralAI(api_key=os.environ.get("MISTRAL_API_KEY"), model="mistral-large-latest")

scrape_website_tool = ScrapeWebsiteTool()
search_tool = SerperDevTool()

# Define agents with specific tools and goals
linkedin_scraper_agent = Agent(
    role="LinkedIn Post Scraper",
    goal="Scrape and extract featured posts from LinkedIn profiles to analyze writing styles and content structures",
    backstory="I am a specialized agent designed to extract featured posts from LinkedIn profiles. I can navigate profiles, find the featured section, and extract posts for analysis.",
    verbose=True,
    allow_delegation=False,
    tools=[scrape_linkedin_posts_tool],
    llm=openai_llm
)

web_researcher_agent = Agent(
    role="Web Researcher",
    goal="Research topics on the web and gather comprehensive, factual, and up-to-date information",
    backstory="I am an expert web researcher who can find, analyze, and summarize information from various online sources. I ensure the information I provide is accurate, relevant, and well-organized.",
    verbose=True,
    allow_delegation=False,
    llm=openai_llm
)

doppelganger_agent = Agent(
    role="LinkedIn Post Creator",
    goal="Create engaging LinkedIn posts that match the writing style of the target profile while incorporating researched information",
    backstory="I am a skilled content creator who specializes in mimicking writing styles. I analyze existing content to understand tone, structure, and style patterns, then create new content that appears to be written by the same author.",
    verbose=True,
    allow_delegation=False,
    llm=openai_llm
)
