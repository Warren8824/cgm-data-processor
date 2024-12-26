"""Basic setup file"""

from setuptools import find_packages, setup

setup(
    name="cgm_data_processor",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        "pandas",
        "numpy",
        "sqlalchemy",
        "plotly",
    ],
    extras_require={
        "dev": [
            "pylint",
            "black",
            "isort",
        ]
    },
)
