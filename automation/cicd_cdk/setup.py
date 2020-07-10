import setuptools


with open("README.md") as fp:
    long_description = fp.read()


setuptools.setup(
    name="cicd_cdk",
    version="1.1.3rev0",

    description="A CDK Python app",
    long_description=long_description,
    long_description_content_type="text/markdown",

    author="author",

    package_dir={"": "cicd_cdk"},
    packages=setuptools.find_packages(where="cicd_cdk"),

    install_requires=[
        "aws-cdk.core<2",
    ],

    python_requires=">=3.6",

    classifiers=[
        "Development Status :: 4 - Beta",

        "Intended Audience :: Developers",

        "License :: OSI Approved :: Apache Software License",

        "Programming Language :: JavaScript",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",

        "Topic :: Software Development :: Code Generators",
        "Topic :: Utilities",

        "Typing :: Typed",
    ],
)
