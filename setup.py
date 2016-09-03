from setuptools import setup

setup(
    version="0.0.1",
    name="duplicity_manager",
    author="Celogeek",
    author_email="me@celogeek.com",
    entry_points = {
        'console_scripts': [
            'duplicity-manager = duplicity_manager:main'
        ]
    },
    py_modules=["duplicity_manager"],
    install_requires=[
        "pyyaml",
        "duplicity>=0.7.10"
    ]
)