FROM python:3.5
ENV PYTHONUNBUFFERED 1
ENV MEDIA_ROOT /data
ENV STATIC_ROOT /tmp/static
# Comment out following line in production:
ENV DEBUG True
VOLUME /data
EXPOSE 8000
WORKDIR /code
RUN apt-get update && apt-get install -y \
  libgdal-dev \
  python-gdal
RUN curl -O https://raw.githubusercontent.com/vishnubob/wait-for-it/master/wait-for-it.sh && chmod u+x wait-for-it.sh
RUN pip install uwsgi psycopg2
ADD . /code/
RUN pip install -r requirements.txt
ENTRYPOINT \
	python manage.py collectstatic --noinput -v0 && \
	(if [ ! -z "$WAIT_FOR_IT" ]; then exec ./wait-for-it.sh "$WAIT_FOR_IT"; exec true; fi) && \
	python manage.py migrate --noinput && \
	uwsgi --master --wsgi paatos.wsgi --http :8000 --enable-threads --workers 4 --die-on-term --need-app --thunder-lock --static-map /static=/tmp/static --static-map /media=/data

# Add "--disable-logging" to this in production:
#	uwsgi --master --wsgi paatos.wsgi --http :8000 --enable-threads --workers 4 --disable-logging --die-on-term --need-app --thunder-lock --static-map /static=/tmp/static --static-map /media=/data
