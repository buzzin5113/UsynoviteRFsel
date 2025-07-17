FROM python:3.11.2-slim-buster
#FROM python:3.10-bullseye
RUN mkdir /app
WORKDIR /app



RUN apt-get update
RUN apt install -y gconf-service libasound2 libatk1.0-0 libc6 libcairo2 libcups2 libdbus-1-3 libexpat1 libfontconfig1 libgcc1 libgconf-2-4 libgdk-pixbuf2.0-0 libglib2.0-0 libgtk-3-0 libnspr4 libpango-1.0-0 libpangocairo-1.0-0 libstdc++6 libx11-6 libx11-xcb1 libxcb1 libxcomposite1 libxcursor1 libxdamage1 libxext6 libxfixes3 libxi6 libxrandr2 libxrender1 libxss1 libxtst6 ca-certificates fonts-liberation libappindicator1 libnss3 lsb-release xdg-utils wget

COPY requirements.txt /app/requirements.txt
COPY main.py /app/main.py
COPY run.sh /app/run.sh
RUN pip install --upgrade pip
RUN pip install -r /app/requirements.txt
#RUN apk -U add chromium udev ttf-freefont
#CMD python /app/main.py
CMD /app/run.sh
