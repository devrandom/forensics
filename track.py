#!/usr/bin/env python3

import json
import os
from os import path

from requests import Session


class Esplora:
    def __init__(self):
        self.session = Session()
        self.base = 'https://blockstream.info/api/'
        self.omit_busy_addresses = os.environ.get('OMIT_BUSY_ADDRESSES') is not None

    def get_txs_for_address(self, address, min_height=None):
        res = self.session.get(f'{self.base}address/{address}/txs/chain')
        jtxs = res.json()
        if min_height:
            #print([t['status']['block_height'] for t in jtxs])
            jtxs = [t for t in jtxs if t['status']['block_height'] >= min_height]
        txs = [self._cvt_tx(tx) for tx in jtxs]
        if len(txs) == 25:
            if self.omit_busy_addresses:
                print(f'skipping busy address {address}')
                return []
            else:
                # TODO chain by last seen
                print(f'warning: tx list for {address} truncated at 25')

        return txs

    def _cvt_tx(self, j):
        outs = []
        for o in j['vout']:
            address = o.get('scriptpubkey_address')
            if address:
                outs.append({'address': address, 'value': o['value']})
            else:
                print(f'vout without an address for tx {j["txid"]}')
        return {
            'txid': j['txid'],
            'outs': outs
        }


class Tracker:
    """Track addresses associated with a seed address list"""
    def __init__(self, min_height, min_value):
        self.client = Esplora()
        self.min_height = min_height
        self.min_value = min_value
        with open('seed-addresses') as f:
            self.addresses = set([l.strip() for l in f.readlines()])
        self.txmap = {}
        if path.exists('txmap'):
            with open('txmap') as f:
                self.txmap = json.load(f)
            self._write_txmap()
            for outs in self.txmap.values():
                for out in outs:
                    if out['value'] > self.min_value:
                        self.addresses.add(out['address'])

        self.seen_addresses = set()

    def run(self):
        did_change = True
        while did_change:
            did_change = False
            print(f'########## addresses {len(self.addresses)} seen {len(self.seen_addresses)}')
            for address in self.addresses.copy():
                if not address in self.seen_addresses:
                    self.seen_addresses.add(address)
                    did_change = self.handle_address(address) or did_change
            self._write_txmap()

        print('########## Report')
        for outs in self.txmap.values():
            for out in outs:
                if out['value'] > self.min_value:
                    print(f"{out['address']} {out['value']/100000000.0}")

    def _write_txmap(self):
        with open('txmap.new', 'w') as f:
            json.dump(self.txmap, f, indent=2)
        os.rename('txmap.new', 'txmap')

    def handle_address(self, address):
        # print(f'handle address {address}')
        txs = self.client.get_txs_for_address(address, self.min_height)
        did_change = False
        for tx in txs:
            txid = tx['txid']
            if not txid in self.txmap:
                # print(f'new tx {txid}')
                did_change = True
                self.txmap[txid] = tx['outs']
                for out in tx['outs']:
                    if out['value'] > self.min_value:
                        #print(f'{out["address"]} {out["value"]}')
                        self.addresses.add(out['address'])
        # print(f'change {did_change}')
        return did_change


def run():
    min_height = 575000
    env_min_height = os.environ.get('MIN_HEIGHT')
    if env_min_height:
        min_height = int(env_min_height)
    # minimum 1 BTC
    min_value = int(os.environ.get('MIN_VALUE', 100000000))
    print(f'min height {min_height}, min value {min_value}')
    Tracker(min_height, min_value).run()


if __name__ == '__main__':
    run()
