"""starlette_cramjam module."""

from setuptools import find_packages, setup

with open("README.md") as f:
    readme = f.read()

# Runtime Requirements.
inst_reqs = ["starlette", "cramjam>=2.4.0,<2.5"]

# Extra Requirements
extra_reqs = {
    "test": ["pytest", "pytest-cov", "requests", "brotlipy"],
    "dev": ["pytest", "pytest-cov", "requests", "brotlipy", "pre-commit"],
}


setup(
    name="starlette_cramjam",
    description=u"Cramjam integration for Starlette ASGI framework.",
    long_description=readme,
    long_description_content_type="text/markdown",
    python_requires=">=3",
    classifiers=[
        "Intended Audience :: Information Technology",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: BSD License",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
    ],
    keywords="Cramjam compression ASGI Starlette",
    author="Vincent Sarago",
    author_email="vincent@developmentseed.org",
    url="https://github.com/developmentseed/starlette-cramjam",
    packages=find_packages(exclude=["tests"]),
    include_package_data=True,
    zip_safe=False,
    install_requires=inst_reqs,
    extras_require=extra_reqs,
)
