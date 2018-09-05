## Project 04 - Item Catalog (Book Catalog)

This project is a Flask CRUD application that manages a book catalog in form of a SQL database. The site implements 3rd party authentication.
Start small, and then you can quickly add any upgrades you need 


## Prerequisites

1. Vagrant
2. VirtualBox
3. Python
4. fullstack-nanodegree-vm provided by Udacity

## How to Run

1. Navigate into the vagrant directory and replace the files of the catalog folder with the contents of this zip.
2. vagrant up (inside the vagrant folder)
3. vagrant ssh
4. cd /vagrant/catalog
5. python database_setup.py
6. python dbpop.py (optional - to populate the database with sample data)
7. python application.py

After having completed these steps, the site should be up and running on http://localhost:5000/
