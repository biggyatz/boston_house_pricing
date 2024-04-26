# boston_house_pricing

### Software and tool requirements
1. [github]
2. [vscodeIDE]
3. [herokuaccount]
4. [GitCLI]

create a new environment for the project

```

conda create -p venv python==3.9.6 -y

```
or you can select the venv manually in your vs code environment 

### Install all the package dependencies with the following command
```
pip install -r requiremtns.txt
```
### Then you check for the ML model file and store the model through pickle into reg model.pkl also you need standardization.pkl 
### Then the app.py file containing the front end of the project is ready to deploy the implemented model 


### Deployment part
### These are the things that need to be done on initialization of a cloud-deployed server
### We use gunicorn pure python HTTP server to run pythons WSGI (Web Server Gateway Interface) applications concurrently using multiple processes
### so a process file (proc file) is created to perform this process 

```
web: gunicorn app:app
```
### here
### gunicorn--> creates multiple Python process and distributes the requests into multiple instances as well 
### app:app--> calls the flask application named app and our python file app.py


### To run the entire app with the help of docker actions you need to have a paid version of the heroku and have 3 secret keys 
```heroku_api_key,heroku_email,heroku_name ```
### Then we put it into the secret key section and while performing the GitHub actions will execute the whole main.yaml which successively runs the docker containers with all the images and gunicorn for the processes into the web 
