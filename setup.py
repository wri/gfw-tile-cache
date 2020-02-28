from setuptools import setup, find_packages

setup(
    name="gfw_fire_vector_tiles",
    version="0.1.0",
    description="Tool to render Fire Vector Tiles",
    packages=find_packages(exclude=("tests",)),
    author="Thomas Maschler",
    license="MIT",
    install_requires=[
        "asyncpg==0.20.1",
        "fastapi==0.49.0",
        "mercantile==1.1.2",
        "uvicorn==0.11.3",
    ],
)
