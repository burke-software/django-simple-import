FROM python:3.5

RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app

COPY setup.py /usr/src/app/
RUN pip install -e .

COPY . /usr/src/app

# include RUN for tests as well as CMD so that all test dependencies are
# installed on the image and wont have to be downloaded again every time
# the image is RUN
CMD python setup.py test
