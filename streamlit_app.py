# streamlit_app.py (LinkedIn Posts tab section updated)
import streamlit as st
import requests
import json
import datetime
import uuid
from typing import List, Dict, Optional, Any

# API endpoints
API_URL = "http://localhost:8001"  # FastAPI service URL
LINKEDIN_POSTS_ENDPOINT = f"{API_URL}/linkedin/posts"
GENERATE_POST_ENDPOINT = f"{API_URL}/generate/post"

# Page configuration
st.set_page_config(
    page_title="CrewAI LinkedIn Post Generator",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'About': "CrewAI LinkedIn Post Generator built with CrewAI, FastAPI, and Streamlit"
    }
)

# Initialize session state for history
if 'linkedin_posts_history' not in st.session_state:
    st.session_state.linkedin_posts_history = []

if 'generated_posts_history' not in st.session_state:
    st.session_state.generated_posts_history = []

# Define the app modes as tabs at the top of the page
tab1, tab2 = st.tabs(["LinkedIn Posts", "Generate Post"])

# Tab 1: LinkedIn Posts
with tab1:
    st.title("📊 LinkedIn Posts")
    st.markdown("This page displays LinkedIn posts extracted from your profile using CrewAI agents.")

    # Add a refresh button
    if st.button("Refresh Posts", key="refresh_posts"):
        with st.spinner("Loading LinkedIn posts..."):
            try:
                response = requests.get(LINKEDIN_POSTS_ENDPOINT)
                response.raise_for_status()
                posts = response.json()

                if posts:
                    # Remove duplicates based on title and content
                    unique_posts = []
                    seen_content = set()

                    for post in posts:
                        # Create a content fingerprint using title and first 100 chars of content
                        title = post.get('title', '')
                        content = post.get('content', '')
                        fingerprint = title + (content[:100] if content else "")

                        if fingerprint not in seen_content and fingerprint.strip():
                            seen_content.add(fingerprint)
                            unique_posts.append(post)

                    # Add timestamp to the history entry
                    history_entry = {
                        "id": str(uuid.uuid4()),
                        "timestamp": datetime.datetime.now().isoformat(),
                        "posts": unique_posts,
                        "count": len(unique_posts)
                    }
                    st.session_state.linkedin_posts_history.insert(0, history_entry)
                else:
                    st.warning("No LinkedIn posts found.")
            except Exception as e:
                st.error(f"Error fetching LinkedIn posts: {str(e)}")

    # Display history of LinkedIn posts
    if st.session_state.linkedin_posts_history:
        # Display the most recent fetch first
        latest_fetch = st.session_state.linkedin_posts_history[0]

        # Format timestamp
        fetch_time = datetime.datetime.fromisoformat(latest_fetch['timestamp']).strftime('%Y-%m-%d %H:%M:%S')
        st.subheader(f"Latest Posts (Fetched: {fetch_time})")

        # Success message
        st.info(f"Successfully loaded {latest_fetch['count']} LinkedIn posts!")

        # Display each post with a number and detailed content
        for i, post in enumerate(latest_fetch["posts"]):
            post_id = post.get('post_id', f"post_{i + 1}")
            title = post.get('title', 'LinkedIn Post')
            truncated_title = title[:50] + ("..." if len(title) > 50 else "")

            # Create an expander for each post
            with st.expander(f"Post {i + 1}"):
                # Create a row with columns for title and dropdown
                col1, col2 = st.columns([4, 1])

                with col1:
                    st.markdown(f"### {title}")

                with col2:
                    # Add dropdown menu with actions
                    if 'actions' in post and post['actions']:
                        action = st.selectbox(
                            "Actions",
                            options=post.get('actions', ["Share", "Copy", "Edit", "Delete"]),
                            key=f"dropdown_{post_id}"
                        )

                        # Add an Apply button for the selected action
                        if st.button("Apply", key=f"apply_{post_id}"):
                            if action == "Share":
                                st.success(f"Shared post: {title}")
                            elif action == "Copy":
                                st.code(post.get('content', ''), language=None)
                                st.success("Content copied to clipboard!")
                            elif action == "Edit":
                                st.info(f"Edit functionality for post: {title}")
                            elif action == "Delete":
                                st.warning(f"Delete functionality for post: {title}")

                # Display timestamp if available
                if 'timestamp' in post:
                    try:
                        post_time = datetime.datetime.fromisoformat(post['timestamp']).strftime('%Y-%m-%d %H:%M:%S')
                        st.markdown(f"**Date:** {post_time}")
                    except:
                        st.markdown(f"**Date:** {post['timestamp']}")

                # Display URL if available
                if 'url' in post and post['url']:
                    st.markdown(f"**Post URL:** [{post['url']}]({post['url']})")

                # Display content URLs if available
                if 'content_urls' in post and post['content_urls']:
                    st.markdown("**Mentioned URLs:**")
                    for idx, url in enumerate(post['content_urls']):
                        st.markdown(f"{idx + 1}. [{url}]({url})")

                # Display any other metadata fields
                for key, value in post.items():
                    if key not in ['title', 'content', 'timestamp', 'url', 'content_urls', 'index', 'post_id',
                                   'actions'] and value:
                        st.markdown(f"**{key.capitalize()}:** {value}")

                # Display full content with proper formatting
                st.markdown("**Content:**")
                content = post.get('content', 'No content')

                # Format content to preserve any structure it may have
                if isinstance(content, str):
                    # Check if content has bullet points or numbered lists
                    if '•' in content or any(line.strip().startswith(str(n) + '.') for n in range(1, 10) for line in
                                             content.split('\n')):
                        st.markdown(content)
                    else:
                        # Display paragraphs with proper spacing
                        paragraphs = content.split('\n\n')
                        for paragraph in paragraphs:
                            if paragraph.strip():
                                st.markdown(paragraph)
                                st.markdown("")
                else:
                    st.json(content)  # If it's not a string, display as JSON
    else:
        st.info("Click 'Refresh Posts' to fetch LinkedIn posts.")

# Tab 2: Generate Post
with tab2:
    st.title("✨ Generate LinkedIn Post")
    st.markdown(
        "This tool generates a professional LinkedIn post based on your writing style and a topic of your choice.")

    # Input form for topic and description
    with st.form(key="post_form"):
        topic = st.text_input("Topic", placeholder="E.g., Artificial Intelligence, Career Growth, Leadership")
        description = st.text_area("Additional Description (optional)",
                                   placeholder="Add more details or context for your post topic...")

        # Submit button
        submit_button = st.form_submit_button(label="Generate Post")

    # Handle form submission
    if submit_button:
        if not topic:
            st.error("Please enter a topic to generate a post.")
        else:
            # Create request payload
            payload = {
                "topic": topic,
                "description": description if description else None
            }

            # Show spinner while generating
            with st.spinner(f"Generating LinkedIn post about '{topic}'... This may take a minute or two."):
                try:
                    # Make API request
                    response = requests.post(
                        GENERATE_POST_ENDPOINT,
                        json=payload,
                        headers={"Content-Type": "application/json"}
                    )
                    response.raise_for_status()

                    # Parse response
                    result = response.json()

                    # Add to history with unique ID
                    history_entry = {
                        "id": str(uuid.uuid4()),
                        "timestamp": datetime.datetime.now().isoformat(),
                        "topic": topic,
                        "description": description,
                        "result": result
                    }
                    st.session_state.generated_posts_history.insert(0, history_entry)

                    # Display success message
                    st.success("Post generated successfully!")

                except Exception as e:
                    st.error(f"Error generating post: {str(e)}")
                    st.info("The API service might be busy or unavailable. Please try again later.")

    # Display history of generated posts
    if st.session_state.generated_posts_history:
        # Display most recent generation first
        latest_generation = st.session_state.generated_posts_history[0]
        result = latest_generation["result"]

        st.subheader("Your Generated Post")
        st.markdown(result.get("generated_post", "No post generated"))

        # Research section (collapsible)
        with st.expander("Research Details"):
            st.markdown(result.get("research_result", "No research results available"))

        # LinkedIn posts that influenced the style
        st.subheader("LinkedIn Posts Used for Style Reference")
        linkedin_posts = result.get("linkedin_posts", [])

        # Remove duplicates
        unique_posts = []
        seen_content = set()

        for post in linkedin_posts:
            # Create a content fingerprint using title and first 100 chars of content
            title = post.get('title', '')
            content = post.get('content', '')
            fingerprint = title + (content[:100] if content else "")

            if fingerprint not in seen_content and fingerprint.strip():
                seen_content.add(fingerprint)
                unique_posts.append(post)

        # Display each unique post in separate expanders (not nested)
        for i, post in enumerate(unique_posts):
            title = post.get('title', 'No title')

            with st.expander(f"Post {i + 1}: {title}"):
                # Display all available fields
                st.markdown(f"**Title:** {title}")

                # Display timestamp if available
                if 'timestamp' in post:
                    try:
                        post_time = datetime.datetime.fromisoformat(post['timestamp']).strftime('%Y-%m-%d %H:%M:%S')
                        st.markdown(f"**Date:** {post_time}")
                    except:
                        st.markdown(f"**Date:** {post['timestamp']}")

                # Display URL if available
                if 'url' in post and post['url']:
                    st.markdown(f"**Link:** [{post['url']}]({post['url']})")

                # Display content
                st.markdown("**Content:**")
                content = post.get('content', 'No content')
                st.markdown(content)

                # Display any other fields
                for key, value in post.items():
                    if key not in ['title', 'content', 'timestamp', 'url'] and value:
                        st.markdown(f"**{key.capitalize()}:** {value}")

        # Add information about when the post was generated
        st.caption(
            f"Generated on: {datetime.datetime.fromisoformat(result.get('timestamp', datetime.datetime.now().isoformat())).strftime('%Y-%m-%d %H:%M:%S')}")

        # Show previous generations in an expander
        if len(st.session_state.generated_posts_history) > 1:
            with st.expander("View Generation History"):
                for i, history_item in enumerate(st.session_state.generated_posts_history[1:], 1):
                    topic_str = history_item["topic"]
                    timestamp = datetime.datetime.fromisoformat(history_item["timestamp"]).strftime('%Y-%m-%d %H:%M:%S')

                    # Create a container for each previous generation
                    st.markdown(f"**Generation {i}** - Topic: '{topic_str}' ({timestamp})")

                    if st.button(f"Show Generation {i}", key=f"show_gen_{i}"):
                        prev_result = history_item["result"]
                        st.markdown("**Generated Post:**")
                        st.markdown(prev_result.get("generated_post", "No post generated"))

                        st.markdown("**Research Details:**")
                        st.markdown(prev_result.get("research_result", "No research results available"))

                        # Display reference posts outside of expanders to avoid nesting
                        st.markdown("**LinkedIn Posts Used for Style Reference:**")

                        prev_linkedin_posts = prev_result.get("linkedin_posts", [])

                        # Remove duplicates
                        unique_prev_posts = []
                        seen_prev_content = set()

                        for post in prev_linkedin_posts:
                            # Create a content fingerprint
                            title = post.get('title', '')
                            content = post.get('content', '')
                            fingerprint = title + (content[:100] if content else "")

                            if fingerprint not in seen_prev_content and fingerprint.strip():
                                seen_prev_content.add(fingerprint)
                                unique_prev_posts.append(post)

                        # Display simplified list of posts
                        for j, post in enumerate(unique_prev_posts):
                            st.markdown(f"**Post {j + 1}: {post.get('title', 'No title')}**")
                            st.markdown(f"{post.get('content', 'No content')[:200]}...")
                            if 'url' in post and post['url']:
                                st.markdown(f"[Link to post]({post['url']})")
                            st.markdown("---")
    else:
        st.info("Fill out the form and click 'Generate Post' to create your first LinkedIn post.")

# Add footer
st.markdown("---")
st.markdown("Built with ❤️ using CrewAI, FastAPI, and Streamlit")