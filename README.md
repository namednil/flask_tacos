This is the backend of the TaCoS 29 webpage, it receives the data from the registration forms and stores the information in a little sqlite database.

The code lives in `__init__.py` and has many things hard-gecoded :/ 

# Setup
Clone this directory into your home directory.
In your home directory, create a folder called `instance`.

Open `__init__.py` and change all e-mail addresses such that __you__ get the e-mails :)

Edit `start_server.sh` to reflect your https setup and move it to your home directory as well, and execute it. To stop the server, open the screen session (`screen -r`) and press CTRL+C.

The file `fees.txt` keeps track of who already payed the fee. 

In order to make it work with mybb forum (registered users get automatically registered there), put `create_users.php` in your mybb root directory and adapt the `create_csv_for_mybb` function.

TODO: check if this actually works as described...
