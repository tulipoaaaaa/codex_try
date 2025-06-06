# File: setup.py

from setuptools import setup, find_packages

setup(
    name="CryptoFinanceCorpusBuilder",
    version="3.0.0",
    description="A desktop application for building and managing a crypto-finance corpus",
    author="Your Name",
    author_email="your.email@example.com",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        # 'PyQt6>=6.6.0',
        # 'PyQt6-Charts>=6.6.0',
        "PyYAML>=6.0",
        "python-dotenv>=1.0.0",
        "PyPDF2>=3.0.0",
        "pytesseract>=0.3.10",
        "pdfminer.six>=20221105",
        "Pillow>=10.0.0",
        "numpy>=1.24.0",
        "scipy>=1.11.0",
        "scikit-learn>=1.3.0",
        "nltk>=3.8.0",
        "spacy>=3.7.0",
        "langdetect>=1.0.9",
        "sympy>=1.12",
        "requests>=2.31.0",
        "beautifulsoup4>=4.12.0",
        "gitpython>=3.1.40",
        "lxml>=4.9.0",
    ],
    python_requires=">=3.8",
    entry_points={
        "console_scripts": [
            "corpus-builder=app.main:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Financial and Insurance Industry",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)
