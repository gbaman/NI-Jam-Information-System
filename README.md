# Northern Ireland Raspberry Jam Information System
An experimental internal management system for the Northern Ireland Raspberry Jam team to use to handle workshops, course materials and attendee information.   
[Proposed spec](NIJIS-spec.md)   

The system is based off Python 3, along with Flask, a MySQL DB, SQLAlchemy and the Eventbrite API library.    

## Installation   
To install, run the following command from inside the `ni_jam_information_system` folder.    
```
python setup.py install
```    

To start the project 
```bash
export FLASK_APP=main.py
flask run
```
