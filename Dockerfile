FROM python:3.9.5

RUN mkdir -p /usr/src/rapid_data_hub
ENV HOME=/usr/src/rapid_data_hub
WORKDIR $HOME
COPY . $HOME
ENV PYTHONPATH "${PYTHONPATH}:${HOME}"

RUN apt-get update
RUN pip install --upgrade pip setuptools wheel
RUN pip install -r requirements.txt

RUN chmod +x /usr/src/rapid_data_hub/prestart.sh
