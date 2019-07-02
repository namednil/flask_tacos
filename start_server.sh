screen -d -m bash -c 'pip install -e ~/flask_tacos/ ; 
	wait && pkill gunicorn ; 
	gunicorn --certfile tacos2019.coli.uni-saarland.de/cert.pem --keyfile tacos2019.coli.uni-saarland.de/privkey.pem -b 0.0.0.0:8080 --log-level=debug start &>> server.log'
