FROM huelse/seal-python
# Requires building the 'huelse/seal-python' docker image as defined at https://github.com/Huelse/SEAL-Python

# Install tcpdump
RUN apt-get update && \
    apt-get install -y \
    tcpdump \
    iproute2 \
    --no-install-recommends

WORKDIR /code

# Install necessary python modules
RUN pip3 install setuptools wheel
RUN pip3 install numpy flask flask_restful requests sqlalchemy xlrd xlsxwriter phe pyope jsonpickle tcconfig
