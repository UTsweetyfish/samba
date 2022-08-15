#!/bin/sh
# rebuild a zone file, adding all DCs

[ $# -eq 2 ] || {
    echo "rebuild_zone.sh <sam.ldb> <zonefile>"
    exit 1
}

LDB="$1"
ZFILE="$2"

dnshostname=$(bin/ldbsearch -H $LDB --scope=base -b '' dnsHostname | grep ^dns | cut -d' ' -f2)
host=$(echo $dnshostname | cut -d. -f1)
realm=$(echo $dnshostname | cut -d. -f2-)
GUIDs=$(bin/ldbsearch -H $LDB objectclass=ntdsdsa objectguid --cross-ncs|grep ^objectGUID| cut -d' ' -f2)
DOMAINGUID=$(bin/ldbsearch -H $LDB --scope=base objectguid |grep ^objectGUID| cut -d' ' -f2)

dcname() {
    GUID=$1
    echo $(bin/ldbsearch -H $LDB objectguid=$GUID dn --cross-ncs|grep CN=NTDS.Settings| cut -d, -f2| cut -d= -f2)
}

getip() {
    NAME=$1
    ret=$(nmblookup $NAME| egrep '^[0-9]' | head -1 | cut -d' ' -f1)
    test -n "$ret" || {
	echo "Unable to find IP for $NAME. Using XX.XX.XX.XX. Please edit" 1>&2
	echo "XX.XX.XX.XX"
    }
    echo $ret
}

echo "Generating header for host $host in realm $realm"
cat <<EOF > $ZFILE
; -*- zone -*-
; generated by rebuild_zone.sh
\$ORIGIN $realm.
\$TTL 1W
@               IN SOA  @   hostmaster (
                                $(date +%Y%m%d%H)   ; serial
                                2D              ; refresh
                                4H              ; retry
                                6W              ; expiry
                                1W )            ; minimum
			IN NS	$host

EOF

for GUID in $GUIDs; do
    dc=$(dcname $GUID)
    echo "Generating IP for DC $dc"
    ip=$(getip $dc)
    test -n "$ip" || exit 1
    echo "	IN A $ip" >> $ZFILE
done

echo "; IP Addresses" >> $ZFILE
for GUID in $GUIDs; do
    dc=$(dcname $GUID)
    ip=$(getip $dc)
    test -n "$ip" || exit 1
    echo "$dc	IN A $ip" >> $ZFILE
done

for GUID in $GUIDs; do
    dc=$(dcname $GUID)
    ip=$(getip $dc)
    test -n "$ip" || exit 1
    echo "Generating zone body for DC $dc with IP $ip"
cat <<EOF >> $ZFILE
;
; Entries for $dc
gc._msdcs		IN A	$ip
$GUID._msdcs	IN CNAME	$dc
_gc._tcp		IN SRV 0 100 3268	$dc
_gc._tcp.Default-First-Site-Name._sites	IN SRV 0 100 3268	$dc
_ldap._tcp.gc._msdcs	IN SRV 0 100 389	$dc
_ldap._tcp.Default-First-Site-Name._sites.gc._msdcs	IN SRV 0 100 389 $dc
_ldap._tcp		IN SRV 0 100 389	$dc
_ldap._tcp.dc._msdcs	IN SRV 0 100 389	$dc
_ldap._tcp.pdc._msdcs	IN SRV 0 100 389	$dc
_ldap._tcp.$DOMAINGUID.domains._msdcs		IN SRV 0 100 389 $dc
_ldap._tcp.Default-First-Site-Name._sites		IN SRV 0 100 389 $dc
_ldap._tcp.Default-First-Site-Name._sites.dc._msdcs	IN SRV 0 100 389 $dc
_kerberos._tcp		IN SRV 0 100 88		$dc
_kerberos._tcp.dc._msdcs	IN SRV 0 100 88	$dc
_kerberos._tcp.Default-First-Site-Name._sites	IN SRV 0 100 88	$dc
_kerberos._tcp.Default-First-Site-Name._sites.dc._msdcs	IN SRV 0 100 88 $dc
_kerberos._udp		IN SRV 0 100 88		$dc
_kerberos-master._tcp		IN SRV 0 100 88		$dc
_kerberos-master._udp		IN SRV 0 100 88		$dc
_kpasswd._tcp		IN SRV 0 100 464	$dc
_kpasswd._udp		IN SRV 0 100 464 	$dc
EOF
done

cat <<EOF >> $ZFILE

; kerberos hack
_kerberos		IN TXT	$(echo $realm | tr [a-z] [A-Z])
EOF

echo "Rebuilt zone file $ZFILE OK"

echo "Reloading bind config"
PATH="/usr/sbin:$PATH" rndc reload
exit 0
