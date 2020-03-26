from setuptools import setup, find_packages

setup(
    name="gfw_fire_vector_tiles",
    version="0.1.0",
    description="Tool to render Fire Vector Tiles",
    packages=find_packages(exclude=("tests",)),
    author="Thomas Maschler",
    license="MIT",
    install_requires=[
        "aiofiles==0.4.0",
        "asyncpg==0.20.1",
        "fastapi==0.52.0",
        "mercantile==1.1.2",
        "uvicorn==0.11.3",
        "pendulum==2.1.0",
        "shapely==1.7.0",
        "SQLAlchemy==1.3.15",
        "requests==2.23.0",
        "async_lru==1.0.2",
    ],
)
