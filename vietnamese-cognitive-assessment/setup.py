from setuptools import setup, find_packages

setup(
    name="vietnamese-cognitive-assessment",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "librosa>=0.10.0",
        "numpy>=1.24.0",
        "scipy>=1.11.0",
        "scikit-learn>=1.3.0",
        "pandas>=2.0.0",
        "praat-parselmouth>=0.4.3",
        "underthesea>=1.3.5",
        "transformers>=4.30.0",
        "torch>=2.0.0",
        "lexicalrichness>=0.4.0",
    ],
    python_requires=">=3.9",
)


