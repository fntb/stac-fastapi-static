"""stac_fastapi: static module."""

from setuptools import find_namespace_packages, setup

with open("README.md") as f:
    desc = f.read()

install_requires = [
    "requests>=2.32,<3",
    "requests-cache>=1.2,<2",
    "requests_file>=2.1,<3",
    "xxhash>=3.5,<4",
    "pydantic>=2.10,<3",
    "stac_pydantic>=3.1,<4",
    "stac-fastapi.api>=5.1,<6",
    "stac-fastapi.extensions>=5.1,<6",
    "stac-fastapi.types>=5.1,<6",
    "brotli_asgi>=1.4,<2",
    "shapely>=2.0,<3",
    "orjson>=3.10,<4",
    "cql2>=0.3.6,<1"
]

extra_reqs = {
    "dev": [
        "pystac[validation]",
        "pytest",
        "wheel",
        "locust",
        "httpx",
        "numpy>=1.7,<3"
    ],
    "server": ["uvicorn[standard]"],
}


setup(
    name="stac-fastapi.static",
    description="An implementation of STAC API based on the FastAPI framework using a static catalog as backend.",
    long_description=desc,
    long_description_content_type="text/markdown",
    python_requires=">=3.10",
    classifiers=[
        "Intended Audience :: Developers",
        "Intended Audience :: Information Technology",
        "Intended Audience :: Science/Research",
        "Programming Language :: Python :: 3.12",
    ],
    keywords="STAC FastAPI stac-fastapi static fs filesystem",
    author="Pierre Fontbonne",
    author_email="pierre.fontbonne@uca.fr",
    url="https://github.com/fntb/stac-fastapi-static",
    license="etalab-2.0",
    packages=find_namespace_packages(exclude=["test", "stac_test_tools"]),
    zip_safe=False,
    install_requires=install_requires,
    tests_require=extra_reqs["dev"],
    extras_require=extra_reqs,
    entry_points={
        "console_scripts": [
            "stac-fastapi-static=stac_fastapi.static.app:run"
        ]
    },
)
