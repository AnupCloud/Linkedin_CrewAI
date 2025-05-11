from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import json
import time
from datetime import datetime
import warnings
import os
import traceback

# Suppress warnings
warnings.filterwarnings("ignore", message="<built-in function callable> is not a Python type")
warnings.filterwarnings("ignore", category=DeprecationWarning)

# Import from CrewAI
from crewai import Crew, Task

# Import agents and tools
from config.agents import linkedin_scraper_agent, web_researcher_agent, doppelganger_agent
from tools import scrape_linkedin_posts_tool


# Data models
class LinkedInPost(BaseModel):
    title: str
    content: str


class HealthResponse(BaseModel):
    status: str
    version: str
    timestamp: str


class TopicRequest(BaseModel):
    topic: str
    description: Optional[str] = None


class GeneratedPostResponse(BaseModel):
    topic: str
    description: Optional[str] = None
    linkedin_posts: List[LinkedInPost]
    research_result: str
    generated_post: str
    timestamp: str


# In-memory storage
linkedin_posts = []

# Create FastAPI app
app = FastAPI(
    title="CrewAI LinkedIn Post Generator API",
    description="API for generating LinkedIn posts using AI agents",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 1. Health check endpoint
@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Health check endpoint to verify API is running"""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }


# 2. Get LinkedIn Posts endpoint
@app.get("/linkedin/posts", response_model=List[LinkedInPost], tags=["LinkedIn"])
async def get_linkedin_posts():
    """Get scraped LinkedIn posts"""
    global linkedin_posts

    if not linkedin_posts:
        # Run the LinkedIn scraper to get posts
        scrape_task = Task(
            description="Scrape a LinkedIn profile to get some relevant posts",
            agent=linkedin_scraper_agent,
            expected_output="A list of LinkedIn posts from the target profile."
        )

        scrape_crew = Crew(
            agents=[linkedin_scraper_agent],
            tasks=[scrape_task],
            verbose=True
        )

        scrape_result = scrape_crew.kickoff()

        try:
            # Convert CrewOutput to string
            result_str = str(scrape_result)
            print(f"Raw result from crew.kickoff(): {str(scrape_result)[:100]}...")  # Print first 100 chars

            # Check if the result is empty or indicates no posts were found
            if result_str.strip() in ["[]", ""] or "no linkedin posts available" in result_str.lower():
                # Create a default post with information about the profile
                profile_name = os.environ.get('LINKEDIN_PROFILE_NAME', 'the target profile')
                linkedin_posts = [{
                    "title": "LinkedIn Profile Information",
                    "content": f"This is placeholder content as no posts were found on the LinkedIn profile {profile_name}. You might want to check if the profile has any public posts or try a different profile."
                }]
                print("Created placeholder post since LinkedIn scraper returned no posts")
            else:
                # Try to find a JSON array first
                start_idx = result_str.find('[')
                end_idx = result_str.rfind(']') + 1

                if start_idx >= 0 and end_idx > start_idx:
                    # Try to parse as JSON
                    json_str = result_str[start_idx:end_idx]
                    try:
                        result = json.loads(json_str.replace("'", "\""))
                        linkedin_posts = result
                        print(f"Successfully parsed JSON array with {len(linkedin_posts)} posts")
                    except json.JSONDecodeError as json_err:
                        print(f"JSON parsing error: {json_err}")
                        # Fall back to text parsing
                        linkedin_posts = []
                else:
                    print("No JSON array found, trying to parse as numbered list...")
                    linkedin_posts = []

                    # Parse as a numbered list (Format: "1. Title\nContent")
                    import re

                    # Pattern to match numbered items with titles and content
                    pattern = r'(\d+)\.\s+(.*?)(?=\s*\n\d+\.\s+|\s*$)'
                    matches = re.findall(pattern, result_str, re.DOTALL)

                    if matches:
                        for num, content in matches:
                            # Split the content into title and body
                            lines = content.strip().split('\n', 1)
                            title = lines[0].strip()
                            body = lines[1].strip() if len(lines) > 1 else ""

                            linkedin_posts.append({
                                "title": title,
                                "content": body
                            })
                        print(f"Successfully parsed text list with {len(linkedin_posts)} posts")
                    else:
                        # Try another pattern for numbered lists
                        pattern = r'(\d+)\.\s+(.*?)\n(.*?)(?=\n\d+\.\s+|\Z)'
                        matches = re.findall(pattern, result_str, re.DOTALL)

                        if matches:
                            for num, title, content in matches:
                                linkedin_posts.append({
                                    "title": title.strip(),
                                    "content": content.strip()
                                })
                            print(f"Successfully parsed text list (alt pattern) with {len(linkedin_posts)} posts")
                        else:
                            print("Could not parse as numbered list either")
                            # If all else fails, create a single post from the entire content
                            linkedin_posts = [{
                                "title": "LinkedIn Post",
                                "content": result_str.strip()
                            }]

                # If linkedin_posts is still empty after all parsing attempts, create a default post
                if not linkedin_posts:
                    profile_name = os.environ.get('LINKEDIN_PROFILE_NAME', 'the target profile')
                    linkedin_posts = [{
                        "title": "LinkedIn Profile Information",
                        "content": f"This is placeholder content as no posts were found on the LinkedIn profile {profile_name}. You might want to check if the profile has any public posts or try a different profile."
                    }]
                    print("Created fallback post after parsing attempts failed")

                # Deduplicate posts
                unique_posts = []
                seen_content = set()
                for post in linkedin_posts:
                    # Create a content fingerprint using title and first 100 chars of content
                    fingerprint = post.get("title", "") + (post.get("content", "")[:100] if post.get("content") else "")
                    if fingerprint not in seen_content:
                        seen_content.add(fingerprint)
                        unique_posts.append(post)

                if unique_posts:
                    linkedin_posts = unique_posts
                    print(f"After deduplication: {len(linkedin_posts)} unique posts")

        except Exception as e:
            print(f"Error parsing LinkedIn posts: {e}")
            # Create fallback content instead of failing
            profile_name = os.environ.get('LINKEDIN_PROFILE_NAME', 'the target profile')
            linkedin_posts = [{
                "title": "LinkedIn Profile Information",
                "content": f"Could not parse LinkedIn posts properly. This is a fallback content generated because an error occurred: {str(e)}"
            }]

    return linkedin_posts


# 3. Generate Post endpoint
@app.post("/generate/post", response_model=GeneratedPostResponse, tags=["Posts"])
async def generate_post(request: TopicRequest):
    """
    Generate a LinkedIn post about a specific topic using three agents in sequence:

    1. LinkedIn Scraper Agent: Scrapes your LinkedIn profile posts to learn your writing style
    2. Web Researcher Agent: Gathers high-quality information about the requested topic
    3. LinkedIn Influencer Agent: Creates a post about the topic in your writing style
    """
    if not request.topic:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Topic is required"
        )

    try:
        # Step 1: Get LinkedIn posts to understand the writing style
        print(f"Step 1: Getting LinkedIn posts to understand the writing style...")

        # Get existing LinkedIn posts from the endpoint
        print("Getting LinkedIn posts from endpoint...")
        endpoint_posts = await get_linkedin_posts()

        # Convert posts to dictionaries with proper formatting including index
        linkedin_posts = []
        for i, post in enumerate(endpoint_posts):
            if hasattr(post, 'dict'):  # If it's a Pydantic model
                post_dict = post.dict()
            else:  # If it's already a dict
                post_dict = post

            # Create a formatted post with index, title, and content clearly separated
            formatted_post = {
                "title": f"{i + 1}. {post_dict.get('title', 'LinkedIn Post')}",
                "content": post_dict.get('content', '')
            }
            linkedin_posts.append(formatted_post)

        print(f"Found {len(linkedin_posts)} posts from endpoint")

        # Step 2: Use Web Researcher Agent to gather information about the topic
        print(f"Step 2: Researching topic: {request.topic}...")

        research_task = Task(
            description=f"Research the topic '{request.topic}' and provide comprehensive, factual information.",
            agent=web_researcher_agent,
            expected_output="A well-structured research document with key facts, insights, and information about the requested topic."
        )

        if request.description:
            research_task.description += f" Additional context: {request.description}"

        # Step 3: Create post generation task
        post_creation_task = Task(
            description=f"Create an engaging LinkedIn post about '{request.topic}' that mimics the writing style from the provided LinkedIn posts. The posts showcase the style to mimic and are:\n\n" +
                        "\n\n".join([f"Post {post.get('title')}\nContent: {post.get('content')}"
                                     for i, post in enumerate(linkedin_posts)]),
            agent=doppelganger_agent,
            expected_output="A high-quality LinkedIn post about the topic that matches the writing style of the sample posts."
        )

        if request.description:
            post_creation_task.description += f" Additional context for the post: {request.description}"

        # Set context using the proper method
        post_creation_task.context = [research_task]

        # Create a crew with all tasks in sequence
        crew = Crew(
            agents=[web_researcher_agent, doppelganger_agent],
            tasks=[research_task, post_creation_task],
            verbose=True
        )

        # Execute all tasks in sequence
        crew_result = crew.kickoff()

        # Extract results
        try:
            # For newer versions of CrewAI that return a CrewResult object
            if hasattr(crew_result, 'output'):
                result_dict = crew_result.output
                if isinstance(result_dict, dict):
                    research_result_str = result_dict.get(research_task.id, "No research results available")
                    post_result_str = result_dict.get(post_creation_task.id, "No post generated")
                else:
                    # If output is not a dict, assume it's the final task's output
                    research_result_str = "Research completed"
                    post_result_str = str(crew_result.output)
            else:
                # For versions that return a string
                post_result_str = str(crew_result)
                research_result_str = "Research completed"
        except Exception as e:
            print(f"Error extracting crew results: {e}")
            traceback_str = traceback.format_exc()
            print(f"Result extraction traceback: {traceback_str}")
            research_result_str = f"Research on {request.topic}"
            post_result_str = f"LinkedIn post about {request.topic}"

        # Return the complete result
        return {
            "topic": request.topic,
            "description": request.description,
            "linkedin_posts": linkedin_posts,
            "research_result": research_result_str,
            "generated_post": post_result_str,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        print(f"Generate post error: {str(e)}")
        traceback_str = traceback.format_exc()
        print(f"Traceback: {traceback_str}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating post: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn

    print("Starting Uvicorn server...")
    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="info")