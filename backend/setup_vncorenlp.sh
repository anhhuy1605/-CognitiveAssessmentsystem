#!/bin/bash
# Setup script for VnCoreNLP
# Vietnamese NLP library with word segmentation, POS tagging, NER, and parsing

set -e

echo "=============================================="
echo "VnCoreNLP Setup Script"
echo "=============================================="

# Check Java
if ! command -v java &> /dev/null; then
    echo "❌ Java not found. Please install Java 8 or later."
    echo "   Ubuntu/Debian: sudo apt install openjdk-11-jdk"
    echo "   macOS: brew install openjdk@11"
    exit 1
fi

JAVA_VERSION=$(java -version 2>&1 | head -n 1 | cut -d'"' -f2 | cut -d'.' -f1)
echo "✅ Java found (version $JAVA_VERSION)"

# Create VnCoreNLP directory
VNCORENLP_DIR="VnCoreNLP"
mkdir -p "$VNCORENLP_DIR"
cd "$VNCORENLP_DIR"

echo ""
echo "Downloading VnCoreNLP..."

# Download VnCoreNLP JAR
if [ ! -f "VnCoreNLP-1.1.1.jar" ]; then
    echo "Downloading VnCoreNLP-1.1.1.jar..."
    wget -q https://raw.githubusercontent.com/vncorenlp/VnCoreNLP/master/VnCoreNLP-1.1.1.jar
    echo "✅ VnCoreNLP JAR downloaded"
else
    echo "✅ VnCoreNLP JAR already exists"
fi

# Create models directory
mkdir -p models/wordsegmenter
mkdir -p models/postagger
mkdir -p models/ner
mkdir -p models/dep

# Download models
echo ""
echo "Downloading models..."

# Word Segmenter
if [ ! -f "models/wordsegmenter/wordsegmenter.rdr" ]; then
    wget -q -P models/wordsegmenter/ https://raw.githubusercontent.com/vncorenlp/VnCoreNLP/master/models/wordsegmenter/wordsegmenter.rdr
    echo "✅ Word segmenter RDR downloaded"
fi

if [ ! -f "models/wordsegmenter/wordsegmenter.txt" ]; then
    wget -q -P models/wordsegmenter/ https://raw.githubusercontent.com/vncorenlp/VnCoreNLP/master/models/wordsegmenter/wordsegmenter.txt
    echo "✅ Word segmenter TXT downloaded"
fi

# POS Tagger
if [ ! -f "models/postagger/vi-tagger" ]; then
    wget -q -P models/postagger/ https://raw.githubusercontent.com/vncorenlp/VnCoreNLP/master/models/postagger/vi-tagger
    echo "✅ POS tagger downloaded"
fi

# NER
if [ ! -f "models/ner/vi-ner" ]; then
    wget -q -P models/ner/ https://raw.githubusercontent.com/vncorenlp/VnCoreNLP/master/models/ner/vi-ner
    echo "✅ NER model downloaded"
fi

# Dependency Parser
if [ ! -f "models/dep/vi-dep" ]; then
    wget -q -P models/dep/ https://raw.githubusercontent.com/vncorenlp/VnCoreNLP/master/models/dep/vi-dep
    echo "✅ Dependency parser downloaded"
fi

echo ""
echo "=============================================="
echo "VnCoreNLP Setup Complete!"
echo "=============================================="
echo ""
echo "Usage in Python:"
echo "  from vncorenlp import VnCoreNLP"
echo "  annotator = VnCoreNLP('VnCoreNLP/VnCoreNLP-1.1.1.jar',"
echo "                        annotators='wseg,pos,ner,parse')"
echo "  result = annotator.annotate('Xin chào Việt Nam')"
echo "  annotator.close()"
echo ""
echo "Note: Make sure to close() the annotator when done!"

