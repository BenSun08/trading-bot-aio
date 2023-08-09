# Trading bot

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
adev runserver trading_bot
```
Run in production mode
```sh
python -m trading_bot.main
```
## Deployment

Connect to AWS EC2 instance
```sh
ssh -i "trading_bot.pem" ec2-user@ec2-3-25-163-115.ap-southeast-2.compute.amazonaws.com
```

### Cofiguration of **supervisor**
Create the configuration file and includes 
```sh
echo_supervisord_conf > /etc/supervisord.conf
mkdir /etc/supervisord.conf.d/ ## a folder to storage different cofig files

```
Edit the configuration file to includes configuration for different program
```sh
vim /etc/supervisord.conf
```
```conf
;[include]
;files = relative/directory/*.ini
files = /etc/supervisord.conf.d/*.conf
```
#### Configuration for the trading bot program (*/etc/supervisord.conf.d/trading_bot.conf*)
```conf
[program:trading_bot]
directory = /home/ec2-user/codes/trading-bot-aio
command = bash -c 'source env/bin/activate && pip install -r requirements.txt && python -m trading_bot.main'; 启动命>令
process_name=%(program_name)s_%(process_num)02d ;
numprocs = 4
numprocs_start=1
autostart = true     ; 在 supervisord 启动的时候也自动启动
startsecs = 5        ; 启动 5 秒后没有异常退出，就当作已经正常启动了
autorestart = true   ; 程序异常退出后自动重启
startretries = 3     ; 启动失败自动重试次数，默认是 3
redirect_stderr = true  ; 把 stderr 重定向到 stdout，默认 false
stdout_logfile_maxbytes = 20MB  ; stdout 日志文件大小，默认 50MB
stdout_logfile_backups = 5     ; stdout 日志文件备份数
stdout_logfile = /etc/supervisord.conf.d/trading_bot.log
stopwaitsecs=2
```
#### Useful Commands
```sh
ps -ef | grep supervisord # find the process
kill -s SIGTERM [PID]
```

```sh
supervisord -c /etc/supervisord.conf ## run supervisor

supervisorctl update # reload the configuration (after you change the configuration)

supervisorctl start all[/app_name]
supervisorctl status # check the status of processes
supervisorctl stop all[/app_name]

```
### Nginx
```sh
nginx -s quit
nginx -s stop
nginx -s reload

ps -ax | grep nginx
sudo pkill -f nginx
```
#### Configuration
```sh
vim /etc/nginx/nginx.conf
```
### Tmux

new session
```sh
tmux new -s [session-name]
```

detach (*ctrl+b d*)
```sh
tmux detach
```
check all sessions
```sh
tmux ls
```
reconnect to the session
```sh
tmux attach -t [session-name]
```
kill session
```sh
tmux kill -t [session-name]
```
switch session
```sh
tmux switch -t [session-name]
```
rename session
```sh
tmux rename-session - t [new-name]
```

## Database

### Postgres

show tables

```sh
postgres=# \dt
``

