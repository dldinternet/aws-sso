import setuptools


with open("README.md") as fp:
    long_description = fp.read()


setuptools.setup(
    name="cicd_cdk",
    version="1.1.3rev10",

    description="A CDK Python app",
    long_description=long_description,
    long_description_content_type="text/markdown",

    author="author",

    package_dir={"": "cicd_lib"},
    packages=setuptools.find_packages(where="cicd_lib"),

    install_requires=[
        'aws-cdk.core<2',
        'cdk-helper>=0.4.16',
        'python-lambda>=11.7.1rev15',
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
