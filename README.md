# ⚠️ No longer maintained (Repo set to 'Public' for Visibility)

This is the bit_bots backend that creates and mints bit_bots. On Cardano. Dependent on the [BlockFrost](blockfrost.io) service.

**Yes there is an exposed api key in the git history, I've since migrated from that key.**

- [Bitbots.py](#bitbotspy)
- [app.py](#apppy)
- [BlockFrostTools.py](#blockfrosttoolspy)
- [CardanoComms.py](#cardanocommspy)
- [Nft.py](#nftpy)
- [Utility.py](#utilitypy)
- [DBComms.py](#dbcommspy)
- [Wallet.py](#walletpy)
- [MintManager.py](#mintmanagerpy)
- [TestSet.py](#testsetpy)
- [MintTask.py](#minttaskpy)

# 🚀 Launch checklist

Ensure there are no duplicate nfts by running
`SELECT uid FROM nft_status GROUP BY uid HAVING COUNT(uid) > 1`

## Setup sql

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

## Backup sql

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
`flask run --host=<IP> --port=<PORT>`

## Status

- Add owner to status
- Add hash to status
- If restart check in progress
  - Check for hash
  - Use API to look for existence of hash or query the whole policy for the nft

# 🧐 Files

### Bitbots.py

Creates bit_bots from a defined input folder.

- Create each NFT
- Ensure all data is split into payloads and references. Keeping all data on chain, bypassing the 16kb limit.

### app.py

Flask API. Simple BE for bit_bots.art. I.e keep prices and payment address correct.

### BlockFrostTools.py

BlockFrost API wrapper, used to lookup the sender of a given tx to allow nft minting to the correct address.

### CardanoComms.py

Communication with native cardano cli. Basically a Python wrapper for cardano-cli.

### Nft.py

Creates the NFT metadata. Makes the metadata pretty but also appends payloads to ensure it's fully on chain.

### Utility.py

Utility functions for JSON and converting ada values between ada and lace.

### DBComms.py

MySQL database wrapper. Creates two basic tables.

- One table for global state
- Another table for all information needed to track nft minting progress and recover if needed.

### Wallet.py

Handle wallet generation and actions such as sending ada.

### MintManager.py

Runs two treads:

```python
  customer_job_t = Thread(target=self.customer_job, args=())
  mint_job_t = Thread(target=self.mint_job, args=())
```

- Customer job that checks for new customers
- Mint job that mints to known customers

### TestSet.py

Simple script to test generation,

### MintTask.py

A simple script for testing the minting task.

# ⚠️ Issues and notes

- Notice a txoutput to small when using 3 ada? for hash 89a4466c5a6aca862e33daf6fe13705aa01c01af18ecb091f659880a1978b24e
- Remove colour from unique id hex
- Ensure policy matched when testing likely issue is API project name is different to that in tests
- Add a test page for meta v2 testing
- Catch api errors - to test run with unknown policy

- when exporting an svg with functions '\_Image' might be duplicated. So we need to ensure all input files have unique image tags. This is due to the software I have used to generate the base svgs.

### version

- Python 3.8.1
