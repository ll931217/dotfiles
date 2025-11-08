#!/bin/sh

# Scrapes documentation from a URL and converts it to Markdown suitable for aider convention files
# to provide context to the LLM.

if [ $# -eq 0 ]; then
    echo "Usage: $(basename "$0") <URL> [URL...]"
    echo
    echo "Generate aider 'convention' Markdown context from documentation URLs."
    echo "suitable for providing LLM context about a project's conventions and style."
    echo
    echo "Outputs a file in the current directory named like 'technology-name.md'."
    exit 1
fi

aider --detect-urls --no-git --no-auto-commits --yes --message "Please summarize the documentation at the following URL into a concise form suitable for giving an LLM context about a project. Write the summary as Markdown into a .md file with a relevant short kebab-case name like 'technology-name.md'. Where appropriate make sure you include a suite of relevant code examples to help the LLM write code in the suggested style of the project. The result will be concatenated with summaries of other technologies so it should have a clear h1 header indicating the content of this markdown section/file. $*"
