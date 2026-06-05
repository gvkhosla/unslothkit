from setuptools import find_packages, setup

setup(
    name="finetunekit",
    version="0.1.0",
    description="Beginner-friendly CLI for Unsloth fine-tuning projects",
    packages=find_packages(),
    python_requires=">=3.9",
    entry_points={"console_scripts": ["finetunekit=finetunekit.cli:main", "unslothkit=finetunekit.cli:main"]},
)
