# Post-Mortem Analyzer

A Streamlit web application for analyzing post-mortem data and extracting meaningful insights, themes, and recommendations.

## Features

- **Text Analysis**: Upload post-mortem data as a text file for AI-powered analysis
- **Theme Identification**: Automatically identifies common themes and patterns in post-mortem lessons
- **Confidence Scoring**: Assigns confidence levels to identified themes and their supporting examples
- **Summary Generation**: Creates concise summaries of post-mortem findings
- **Recommendations**: Provides actionable recommendations based on analysis
- **Interactive UI**: Organized in tabs for easy navigation through different aspects of the analysis

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/post-mortem-analyzer.git
cd post-mortem-analyzer
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
# On Windows
venv\Scripts\activate
# On macOS/Linux
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file by copying the template:
```bash
cp .env.template .env
```

5. Edit the `.env` file to add your OpenAI API key:
```
OPENAI_API_KEY=your_api_key_here
# Optionally specify a model (defaults to gpt-3.5-turbo)
# OPENAI_MODEL=gpt-4
```

## Usage

1. Start the Streamlit app:
```bash
streamlit run main.py
```

2. Open your browser and navigate to http://localhost:8501

3. Upload a post-mortem text file (.txt) using the file uploader

4. The analysis will automatically run and display results across four tabs:
   - **Unrecoverable Lines**: Lines with no meaningful content
   - **Common Themes**: Identified patterns with confidence scores
   - **Unclassified Lines**: Meaningful content that doesn't fit into identified themes
   - **Summary & Recommendations**: Overall findings and actionable next steps

## Input Format

The application accepts plain text files (.txt) containing post-mortem lessons, observations, or notes. Each line or paragraph should ideally represent a discrete observation or lesson learned.

## How It Works

1. The application takes post-mortem data as input
2. It uses OpenAI's GPT models to analyze the content
3. The analysis includes:
   - Identifying lines with no recoverable meaning
   - Clustering meaningful content into common themes
   - Calculating confidence scores for theme assignments
   - Generating a concise summary
   - Developing observations and recommendations

## Troubleshooting

If you encounter errors:

- **API Key Issues**: Ensure your OpenAI API key in the `.env` file is valid
- **Malformed Response Errors**: Try using a different model by setting `OPENAI_MODEL` in the `.env` file
- **Gateway Errors**: These may be temporary. Retry the analysis or check your network connection
- **Detailed Error Information**: Expand the "Error Details" section when errors occur for more information

## Dependencies

- streamlit: Web application framework
- openai: OpenAI API client for GPT models
- python-dotenv: Environment variable management
- tenacity: Retry mechanism for API calls

## License

[MIT License](LICENSE)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.