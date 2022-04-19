"""
When run in cron, automatically adds compliant alias names to local DNS.
Use at your own risk.

Patrick Fuller, 25 June 17
"""
import re
import paramiko
import pymongo

# TODO: User environment variable for user and hostname.

paths = {
    'mongo': ('localhost', 27117),
    'gateway': {'hostname': '192.168.1.1', 'username': 'user'},
    'leases': '/var/run/dhcpd.leases',
    'config': '/config/config.boot',
    'dnsmasq': '/etc/dnsmasq.d/dnsmasq.static.conf'
}

# Get alias-mac map through mongodb data store
alias_map = {}
db = pymongo.MongoClient(*paths['mongo'])
for client in db.ace.user.find({'name': {'$exists': True}}):
    if re.sub(r'[-.]', '', client['name']).isalnum():
        alias_map[client['name']] = client['mac']
db.close()

# Connect to gateway to start configuration.
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(**paths['gateway'])
sftp_client = client.open_sftp()
try:
    # Get mac-ip map by reading DHCP leases and reservations from config files
    mac_map = {}
    regex = re.compile(r'lease ([0-9.]+) {.*?' +
                       r'hardware ethernet ([:a-f0-9]+);.*?}',
                       re.MULTILINE | re.DOTALL)
    with sftp_client.open(paths['leases']) as in_file:
        leases = in_file.read()
        try:
            leases = leases.decode('utf-8')
        except AttributeError:
            pass
        for match in regex.finditer(leases):
            ip, mac = match.group(1), match.group(2)
            mac_map[mac] = ip
    regex = re.compile(r'static-mapping [-a-f0-9]+ {.*' +
                       r'?ip-address ([0-9.]+).*?' +
                       r'mac-address ([:a-f0-9]+).*?}',
                       re.MULTILINE | re.DOTALL)
    with sftp_client.open(paths['config']) as in_file:
        cfg = in_file.read()
        try:
            cfg = cfg.decode('utf-8')
        except AttributeError:
            pass
        for match in regex.finditer(cfg):
            ip, mac = match.group(1), match.group(2)
            mac_map[mac] = ip

    # Generate dnsmasq config file
    conf = ''.join(['address=/{hn}/{ip}\n'.format(hn=alias, ip=mac_map[mac])
                    for alias, mac in sorted(alias_map.items())
                    if mac in mac_map])

    # Compare with current config. Update and reload if needed.
    try:
        with sftp_client.open(paths['dnsmasq']) as in_file:
            current = in_file.read()
    except IOError:
        current = ''
    if conf.strip() != current.strip():
        print("Reloading dnsmasq.")
        with sftp_client.open('/tmp/dnsmasq', 'w') as out_file:
            out_file.write(conf)
        client.exec_command('sudo cp /tmp/dnsmasq ' + paths['dnsmasq'])
        client.exec_command('sudo /etc/init.d/dnsmasq force-reload')
finally:
    sftp_client.close()
    client.close()