from setuptools import setup, find_packages

setup(
    name = "django-simple-import",
    version = "2.0.1",
    author = "David Burke",
    author_email = "david@burkesoftware.com",
    description = ("A Django import tool easy enough your users could use it"),
    license = "BSD",
    keywords = "django import",
    url = "https://github.com/burke-software/django-simple-import",
    packages=find_packages(),
    include_package_data=True,
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        'Environment :: Web Environment',
        'Framework :: Django',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.5',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        "License :: OSI Approved :: BSD License",
    ],
    install_requires=['django'],
    extras_require = {
        'xlsx': ["openpyxl"],
        'ods': ["odfpy"],
        'xls': ["xlrd"],
    },
)
