# todo

[x] Generate a nft set, with the correct payloads and metadata
[x] Export svg option
[x] Use a database to store state
[x] Working minting function

[] Change all python files to use there own logger with it's own file? and check it works, remove ascii colours as it's too noisy

[] Api interfaces with mint
    [] User requests buy, api returns addr, PRICE + random dust.
        [] DB updates status of next 'available' status to 'reserved'
        [] TX finder jobs runs and looks for payment. On find it changes status in db to 'awaiting-mint' adds customer addr and tx hash
        [] User is notified that they have paid
        [] Mint queue job picks up the task and mints
        [] User is shown their new nft
        [] If no payment after 24 hours price and status are reset

[] Api call to get all payload data...
[] Api call to get all meta (could only do 721 to save data)

[] Graceful stop method, finishes all tasks then returns

[] Test multiple async buys
    [] 10 wallets buy every 20 seconds
    [] each wallet reports it's last action
    [] check wallet action against db to confirm success
[] Test killing app half way through
[] Add logs to db for minting


# Setup sql
Setup mysql
```
sudo apt update
sudo apt install mysql-server
sudo systemctl start mysql.service
sudo mysql_secure_installation
```
Create sql user (as super user)
```
sudo mysql
CREATE USER '<USER>'@'localhost' IDENTIFIED BY '<PASS>';
GRANT ALL PRIVILEGES ON *.* TO '<USER>'@'localhost' WITH GRANT OPTION;
FLUSH PRIVILEGES;
exit
```

Note db lives at
/var/lib/mysql/<DB_NAME>

# Running api
Start api
```flask run --host=<IP> --port=<PORT>```


## status
- Add owner to status
- Add hash to status
- If restart check in progress
    - Check for hash
    - Use API to look for existence of hash or query the whole policy for the nft


## Files
### Bitbots.py
### app.py
### BlockFrostTools.py
### CardanoComms.py
### Nft.py
### Utility.py
### Wallet.py

## Issues and notes
- Notice a txoutput to small when using 3 ada? for hash 89a4466c5a6aca862e33daf6fe13705aa01c01af18ecb091f659880a1978b24e
- Remove colour from unique id hex
- Ensure policy matched when testing likely issue is API project name is different to that in tests
- Add a test page for meta v2 testing
- Catch api errors - to test run with unknown policy

### version
- Python 3.8.10