import os

import setuptools

with open('README.md', 'r') as file:
    description = file.read()

setuptools.setup(
    name='django-autodrp',
    version=os.environ.get('version'),
    author='rcj0003',
    url='https://github.com/rcj0003/django-autodrp',
    description='Automatically set-up filters and permissions for Django\'s DRY Rest Permissions',
    long_description=description,
    long_description_content_type='text/markdown',
    packages=setuptools.find_packages(),
    classifiers=[
        'Programming Language :: Python :: 3',
        'Framework :: Django :: 3.0',
        'Framework :: Django :: 3.2',
        'Framework :: Django :: 4.0',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License'
    ],
    python_requires='>=3.5',
    py_modules=['djanto-autodrp'],
    install_requires=['django>=3.0', 'djangorestframework>=3.12.4']
)
