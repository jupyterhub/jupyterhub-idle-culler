from setuptools import setup, find_packages

setup(
    name="jupyterhub-idle-culler",
    version="1.2.1",
    packages=find_packages(),
    license="3-BSD",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="Jupyter Development Team",
    author_email="jupyter@googlegroups.com",
    url="https://jupyter.org",
    entry_points={
        "console_scripts": [
            "cull_idle_servers.py = jupyterhub_idle_culler:main",
            "jupyterhub-idle-culler = jupyterhub_idle_culler:main",
        ]
    },
    python_requires=">=3.6",
    install_requires=["tornado", "python-dateutil"],
)
