
Activate the virtual environment.
```sh
source env/bin/activate
```
Install the dependencies.
```sh
pip install -r requirements.txt
```

Run local server in development mode
```sh
adev runserver trading_bot/main.py
```

Connect to AWS EC2 instance
```
ssh -i "capstone_trading_bot.pem" ec2-user@ec2-3-26-242-200.ap-southeast-2.compute.amazonaws.com
```