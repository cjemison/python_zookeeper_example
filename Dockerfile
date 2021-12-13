FROM python:3.9.9-slim
RUN mkdir -p /app
RUN mkdir -p /app/lib

ADD main.py /app/main.py
ADD ./lib/*.py /app/lib
ADD entry-point.sh /app/entrypoint.sh
ADD requirements.txt /app/requirements.txt
RUN chmod 777 /app/entrypoint.sh
WORKDIR /app
RUN pip install -r requirements.txt
ENTRYPOINT [ "/bin/bash", "/app/entrypoint.sh" ]