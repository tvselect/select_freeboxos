echo --- crontab start: $(date) >> /var/tmp/cron_freeboxos.log
cd /opt/select_freeboxos
. .venv/bin/activate
export DISPLAY=:0 && python3 freeboxos.py >> /var/tmp/cron_freeboxos.log 2>&1
deactivate
echo --- crontab end: $(date) >> /var/tmp/cron_freeboxos.log
