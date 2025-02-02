
![Python Version](https://img.shields.io/badge/python-3.10-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-1.40.1-ff4b4b?logo=streamlit)
![LangChain](https://img.shields.io/badge/LangChain-v0.2.43-blue?logo=langchain&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-latest-2496ed?logo=docker&logoColor=white)
![Ollama](https://img.shields.io/badge/Ollama-v0.1.0-4b8bbe?logo=code&logoColor=white)
![gTTS](https://img.shields.io/badge/gTTS-v2.5.4-brightgreen?logo=google&logoColor=white)
![DeepL](https://img.shields.io/badge/DeepL-API%20Integration-blue?logo=translate&logoColor=white)
![PyTorch](https://img.shields.io/badge/PyTorch-2.4.1-orange?logo=pytorch&logoColor=white)



# Multi-Agent Museum Assistant

<div align="center">
 <img src="scheme.png" width="750" alt=""/>
</div>

## Overview

The Multi-Agent Museum Assistant project aims to provide an interactive and intelligent assistant for museum visitors. The system leverages multiple agents to enhance the visitor experience by providing detailed information and guidance throughout the museum.

## Features

- **Interactive Assistance**: Provides real-time information and guidance to museum visitors.
- **Multi-Agent System**: Utilizes multiple agents to handle different tasks and improve efficiency.
- **Natural Language Processing**: Uses advanced NLP techniques to understand and respond to visitor queries.

## Installation

To set up the project, follow these steps:

1. **Clone the repository**:
    ```sh
    git clone https://github.com/yourusername/multi-agent-museum-assistant.git
    cd multi-agent-museum-assistant
    ```

2. **Set up the Python environment**:
    ```sh
    python3 -m venv .venv
    source .venv/bin/activate
    ```

3. **Install the dependencies**:
    ```sh
    pip install --no-cache-dir packages/tokenizers-0.9.4-cp38-cp38-manylinux2010_x86_64.whl
    pip install --no-cache-dir -r requirements.txt
    ```

## Usage

To run the application, use the following command:
```sh
streamlit run orchestrator.py