# basically just parse & make it easier to access the DN data from the output of
# "dynodelist full"


class Dynode():
    def __init__(self, collateral, dnstring):
        (txid, vout_index) = self.parse_collateral_string(collateral)
        self.txid = txid
        self.vout_index = int(vout_index)

        (status, protocol, address, ip_port, lastseen, activeseconds, lastpaid) = self.parse_dn_string(dnstring)
        self.status = status
        self.protocol = int(protocol)
        self.address = address

        # TODO: break this out... take ipv6 into account
        self.ip_port = ip_port

        self.lastseen = int(lastseen)
        self.activeseconds = int(activeseconds)
        self.lastpaid = int(lastpaid)

    @classmethod
    def parse_collateral_string(self, collateral):
        (txid, index) = collateral.split('-')
        return (txid, index)

    @classmethod
    def parse_dn_string(self, dn_full_out):
        # trim whitespace
        # dn_full_out = dn_full_out.strip()

        (status, protocol, address, lastseen, activeseconds, lastpaid,
         lastpaidblock, ip_port) = dn_full_out.split()

        # status protocol pubkey IP lastseen activeseconds lastpaid
        return (status, protocol, address, ip_port, lastseen, activeseconds, lastpaid)

    @property
    def vin(self):
        return self.txid + '-' + str(self.vout_index)
