# Blockchain forensics

Naive tracking of blockchain addresses by crawling the transaction
graph starting at that address.

Usage:

Put addresses you want to track in the file `seed-address`.  Optionally set
the environment variable `MIN_HEIGHT` to the minimum block height
you are interested in.  Optionally set the environment variable `OMIT_BUSY_ADDRESSES`
if you want to skip addresses with more than 25 transactions (those may be exchange
hot wallets or such).

Then run:

```sh
./track.py
```

You can kill and restart the process at any time.  Every time a scanning pass is
done, the file `txmap` will be populated with a JSON dump of all transactions
that were found.  `txmap` also acts as the persistent state of the script.

Limitations:

- Only the last 25 transactions are considered for each address
- Exchange wallets and mixers may result in a large number of unwanted hits
