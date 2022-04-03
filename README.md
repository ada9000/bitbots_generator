# Potential usage

- API looks for policy
- IF nfts available to mint mint process starts



# DB schema
?

## status
- Add owner to status
- Add hash to status
- If restart check in progress
    - Check for hash
    - Use API to look for existence of hash or query the whole policy for the nft

## Bitbots
- Todo

## Minting
- Todo


## Issues and notes
- Notice a txoutput to small when using 3 ada? for hash 89a4466c5a6aca862e33daf6fe13705aa01c01af18ecb091f659880a1978b24e
- Remove colour from unique id hex
- Ensure policy matched when testing likely issue is API project name is different to that in tests
- Add a test page for meta v2 testing
- Catch api errors - to test run with unknown policy