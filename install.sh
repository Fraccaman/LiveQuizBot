#!/bin/bash
pip3 install -r requirements.txt
python3 -m nltk.downloader stopwords 
python3 -m nltk.downloader punkt
python3 -m spacy download it_core_news_sm

brew install tesseract
brew install tesseract-lang
brew install homebrew/cask/android-platform-tools
