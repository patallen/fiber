from distutils.core import setup

install_requires = (
    'celery==4.3',
    'requests==2.22.0',
    'sanic==19.9.0',
    'python-socketio==4.3',
    'urllib3==1.25.3',
)

setup(
    install_requires=install_requires,
    name="fiber",
    version="0.0.0dev",
    packages=["fiber"],
    license="MIT",
    long_description=open("README.txt").read(),
    entry_points={
        'console_scripts': [
            'fib = fiber.app:main',
        ],
    },
)
