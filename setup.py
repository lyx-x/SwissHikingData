import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="swisshikingdata",
    version="0.0.1",
    author="Yuxiang Li",
    author_email="li.yuxiang.nj@gmail.com",
    description="Swiss hiking data aggregator.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/lyx-x/SwissHikingData",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
