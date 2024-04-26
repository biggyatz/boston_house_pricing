# boston_house_pricing

### software and tool requirements
1. [github]
2. [vscodeIDE]
3. [herokuaccount]
4. [GitCLI]

create new environment for the project

```

conda create -p venv python==3.9.6 -y

```
or you can select the venv manually in your vs code environment 

### install all the package dependencies with the following command
```
pip install -r requiremtns.txt
```
### then you check for the ML model file and store the model through pickle into reg model.pkl also you need standardization.pkl 
### then the app.py file containing the front end of the project is ready to be deploy the implemented model 


### Deployment part
### these are the things that need to be done on intialization of a cloud deployed server
### we use gunicorn pure python http server to run pythons WSGI (Web Server Gateway Interface) applications concurrently using multiple processes
### so a process file (proc file) is created to perform this proces 

```
web: gunicorn app:app
```
### here
### gunicorn--> creates multiple python process and distributes the requests into multiple instances as well 
### app:app--> calls the flask application named app and our python file app.py
