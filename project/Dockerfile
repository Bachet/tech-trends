# use the python:3.8 base image
FROM python:3.8-slim

WORKDIR /app

# copy all the files from the current directory to the container working directory (e.g. `/app`)
COPY techtrends ./

# install dependencies using `pip install`
RUN pip install -r requirements.txt

# ensure the database is initialized with the pre-defined posts in the init_db.py file and run the flask app afterwards
RUN python init_db.py

# expose the port 3111
EXPOSE 3111

# execute the application at the container start
CMD ["python","app.py"]
