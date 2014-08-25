from setuptools import setup, find_packages

setup(
    name = "django-simple-import",
    version = "1.16",
    author = "David Burke",
    author_email = "david@burkesoftware.com",
    description = ("A Django import tool easy enough your users could use it"),
    license = "BSD",
    keywords = "django import",
    url = "https://github.com/burke-software/django-simple-import",
    packages=find_packages(),
    include_package_data=True,
    test_suite='setuptest.setuptest.SetupTestSuite',
    tests_require=(
        'django-setuptest',
        'south',
    ),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        'Environment :: Web Environment',
        'Framework :: Django',
        'Programming Language :: Python',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        "License :: OSI Approved :: BSD License",
    ],
    install_requires=['django', 'openpyxl', 'odfpy', 'xlrd']
)
