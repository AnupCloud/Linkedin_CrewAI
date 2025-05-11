## 📝 Project Description

This repository contains a comprehensive CrewAI application designed to automate the generation of high-quality LinkedIn posts. The system uses multiple AI agents working together to create content that matches your writing style based on previously published LinkedIn posts.

![Alt text](img/crewai_linkedin.svg)

### How It Works

The application uses a multi-agent system with three specialized AI agents:

1. **LinkedIn Scraper Ninja**: Scrapes your LinkedIn profile to learn from your previous posts using a custom Selenium tool
2. **Web Researcher**: Gathers relevant information about your chosen topic from the web
3. **Influencer Agent**: Combines your writing style with researched information to craft an engaging LinkedIn post

The application includes a web interface built with Streamlit and a backend API powered by FastAPI, making it easy to generate new posts and view your LinkedIn content.

## 🔧 Requirements

### System Requirements
- Python 3.13+
- Chrome browser (for Selenium-based LinkedIn scraping)
- Internet connection

### API Keys
- **OpenAI API Key** - For GPT-4.1 model access
- **Mistral AI API Key** - For Mistral Large model access (Optional)
- **Serper API Key** - For web search capabilities (used by the Web Researcher agent)

### LinkedIn Credentials
- LinkedIn Email
- LinkedIn Password
- LinkedIn Profile Name

## 🔗 Dependencies

The project uses the following major libraries:

- **CrewAI** - Framework for building multi-agent AI systems
- **CrewAI Tools** - Extended tools for CrewAI agents
- **Selenium** - For web scraping LinkedIn
- **FastAPI** - Backend API framework
- **Streamlit** - Web interface
- **LangChain** - For LLM integrations
- **Python-dotenv** - For environment variable management
- **BeautifulSoup4** - For HTML parsing

See `requirements.txt` or `pyproject.toml` for a complete list of dependencies.

## 🚀 Installation

### Option 1: Using pip (Traditional)

1. **Clone the repository**
   ```bash
   git clone https://github.com/AnupCloud/Linkedin_CrewAI.git
   cd Linkedin_CrewAI
   ```

2. **Set up a virtual environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows, use: .venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

### Option 2: Using uv (Faster Installation)

The project includes support for [uv](https://github.com/astral-sh/uv), a faster Python package installer and resolver.

1. **Install uv** (if not already installed)
   ```bash
   pip install uv
   ```

2. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/crewai_linkedin_post.git
   cd crewai_linkedin_post
   ```

3. **Create a virtual environment and install dependencies using uv**
   ```bash
   uv venv
   source .venv/bin/activate  # On Windows, use: .venv\Scripts\activate
   uv add -r requirements.txt
   ```

   Alternatively, use the lockfile for deterministic installs:
   ```bash
   uv sync uv.lock
   ```

4. **Create an environment file**
   Create a `.env` file in the root directory with the following variables:
   ```
   # API Keys
   OPENAI_API_KEY=your_openai_api_key
   MISTRAL_API_KEY=your_mistral_api_key
   SERPER_API_KEY=your_serper_api_key
   
   # LinkedIn Credentials
   LINKEDIN_EMAIL=your_linkedin_email
   LINKEDIN_PASSWORD=your_linkedin_password
   LINKEDIN_PROFILE_NAME=your_linkedin_profile_name
   ```

## 🖥️ Usage

### Option 1: Run via Command Line
To generate a LinkedIn post using the command line:

```bash
python main.py
```

This will execute the full agent workflow and display the generated post in the console.

### Option 2: Use the Web Interface

1. **Start the API server**
   ```bash
   python api.py
   ```

2. **Launch the Streamlit app**
   ```bash
   streamlit run streamlit_app.py
   ```

3. **Access the web interface** at http://localhost:8501

## 📁 Project Structure

- **`main.py`**: Entry point for CLI version, orchestrates the CrewAI agents
- **`api.py`**: FastAPI backend for the web interface
- **`streamlit_app.py`**: Streamlit web interface
- **`config/`**: Configuration directory
  - **`agents.py`**: Defines the three CrewAI agents
  - **`tasks.py`**: Defines the tasks for each agent
- **`tools/`**: Custom tools directory
  - **`linkedin.py`**: LinkedIn scraping tool using Selenium
  - **`utils.py`**: Utility functions
  - **`constant.py`**: Constants used by the tools
- **`requirements.txt`**: Python dependencies
- **`pyproject.toml`**: Project metadata and dependencies
- **`uv.lock`**: Lock file for deterministic dependency installation with uv
- **`.python-version`**: Python version specification
- **`img/`**: Image assets for the project

## 🔍 External APIs

### Serper API
The Web Researcher agent uses the [Serper API](https://serper.dev/) to perform web searches for gathering information about specified topics. Serper provides Google Search results in a structured JSON format, making it easier for the agent to process and extract relevant information.

To set up Serper API:
1. Create an account at [serper.dev](https://serper.dev/)
2. Get your API key from the dashboard
3. Add the API key to your `.env` file as `SERPER_API_KEY=your_key_here`

Serper API is used through the CrewAI Tools integration, which simplifies the process of making search queries and parsing results.

## 📦 Package Management with uv

This project supports [uv](https://github.com/astral-sh/uv), a fast Python package installer and resolver written in Rust. Key benefits include:

- **Speed**: Up to 10-100x faster than pip for installations
- **Lockfile Support**: Deterministic builds via `uv.lock`
- **Compatibility**: Fully compatible with pip and Python's packaging ecosystem

The included `uv.lock` file ensures that all developers use the exact same dependency versions, avoiding "it works on my machine" problems.

To update dependencies with uv:
```bash
uv pip compile requirements.txt -o requirements.txt
uv pip sync
```

## 🛠️ Customization

To customize the LinkedIn post topic:
1. Edit the topic in `main.py` if using the CLI
2. Or use the web interface to specify a new topic and description

For advanced customization, you can modify:
- Agent configurations in `config/agents.py`
- Task definitions in `config/tasks.py`
- LinkedIn scraping behavior in `tools/linkedin.py`

## 🔒 Security Notes

- The application requires storing your LinkedIn credentials in the `.env` file. Always keep this file private and never commit it to version control
- API keys should be kept confidential and never shared
- The application stores LinkedIn posts in memory, not in a database, for simplicity

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is open source and available under the [MIT License](LICENSE).

## 🙏 Acknowledgements

This project utilizes the [CrewAI](https://github.com/joaomdmoura/crewAI) framework for agent coordination and workflow.