# todo
[x] mouths should be mouths
[] merge background colour with planets in effects
[] if bg is planet effect is none
[] IPFS (I guess -_-)
[] Ensure correct release i.e input is no longer called input v3
[x] Fix id position again
[x] if moon remove bg
[x] sort out bg colour
[] emoji tags? lol

[x] ensure replace _ with space in nft traits etc
[] special random strings that are traits...


[] enchantments 0x | defense set
    circuit protection, enchanted surface, 
[] enchantments 0x | offense set
[] bit-flipped option


enchantments
    big brain? | gm? / ngmi? | elven armour | solar | wind |
    agi core | ai core | heat shielding | water resistant | soul encapsulation |
    potato | plant based enhancements | 

technology 
    elven | plant | unknown

rankings
    efficiency
    armour
    health
    intelligence



<g>
id="identification "
transform="translate(220,0)"


[x] Generate a nft set, with the correct payloads and metadata
[x] Export svg option
[x] Use a database to store state
[x] Working minting function
[x] Database integration
[x] Customer search job
[x] Mint job
[] Change all python files to use there own logger with it's own file? and check it works, remove ascii colours as it's too noisy

[] Api call to get all payload data...
[] Api call to get all meta (could only do 721 to save data)

[] Graceful stop method, finishes all tasks then returns

[] Test multiple async buys
    [] 10 wallets buy every 20 seconds
    [] each wallet reports it's last action
    [] check wallet action against db to confirm success
[] Test killing app half way through
[] Add logs to db for minting

# launch checklist
Ensure there are no duplicate nfts by running
```SELECT uid FROM nft_status GROUP BY uid HAVING COUNT(uid) > 1```

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

## backup sql
backup using mysqldump
```
sudo mysqldump TARGET > BACKUP.sql
```
restore, you will need to create the db first in mysql
```
sudo mysql NEW_DB_NAME < BACKUP.sql
```

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

- when exporting an svg with functions '_Image' might be duplicated. So we need to ensure all input files have unique image tags. This is due to the software I have used to generate the base svgs.

### version
- Python 3.8.1