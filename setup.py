from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="fast-autoscaler",
    version="0.2.0",
    author="StepScale.io",
    author_email="info@stepscale.io",
    description="A modular, extensible autoscaling solution for AWS ECS services based on queue metrics",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/stepscale/fast-autoscaler",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=[
        "boto3>=1.26.0",
        "botocore>=1.29.0",
        "retry>=0.9.2",
    ],
)