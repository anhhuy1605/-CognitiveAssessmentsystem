# setup.py
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="vietnamese-speech-transcriber",
    version="2.0.0",
    author="Vietnamese AI Team",
    author_email="ai@vietnamese.com",
    description="Advanced Vietnamese Real-time Speech Transcriber using Whisper",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/vietnamese-ai/speech-transcriber",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Multimedia :: Sound/Audio :: Speech",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": ["pytest>=7.0.0", "black>=23.0.0", "flake8>=5.0.0"],
        "api": ["flask>=2.3.0", "fastapi>=0.100.0", "uvicorn>=0.23.0"],
    },
    entry_points={
        "console_scripts": [
            "vietnamese-transcriber=vietnamese_transcriber:main",
        ],
    },
)
