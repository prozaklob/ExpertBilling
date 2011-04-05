#!/usr/bin/env python
#coding=utf-8

import os
import sys
import shutil
from hashlib import md5
import datetime
import commands
import ConfigParser
import datetime
import psycopg2
import psycopg2.extras

DIST_PATH=os.path.abspath('.')
SQL_UPGRADE_PATH = DIST_PATH+'/sql/upgrade/' 
BILLING_PATH = '/opt/ebs/data'
WEBCAB_PATH = '/opt/ebs/web/'
BACKUP_DIR = '/opt/ebs/backups/'
LAST_SQL = '/opt/ebs/data/sql/last_sql.dont_remove' 
exclude_files=(
'/opt/ebs/data/ebs_config.ini',
'/opt/ebs/data/ebs_config_runtime.ini',
'/opt/ebs/web/ebscab/settings.py',
'/opt/ebs/web/ebscab/upgrade.py',
)
curdate = datetime.datetime.now().strftime('%d-%m-%y_%H_%M_%S')
config = ConfigParser.ConfigParser()
config.read(BILLING_PATH+"/ebs_config.ini") 

try:
    conn = psycopg2.connect("dbname='%s' user='%s' host='%s' password='%s' port='%s'" % (config.get('db', 'name'), config.get('db', 'username'),config.get('db', 'host'),config.get('db', 'password'), config.get('db', 'port')));
    cur=conn.cursor()
except Exception, e:
    print "I am unable to connect to the database"
    print e
    print "Please, enter correct database parameters in %s/ebs_config.ini" % BILLING_PATH
    sys.exit()
        
def modification_date(filename):
    t = os.path.getctime(filename)
    return datetime.datetime.fromtimestamp(t)

def md5gen(file_path):
    f = open(file_path,'rb')
    
    data=f.read()
    f.close()
    return md5(data).digest()

def stop_processes():
    print '*'*80
    print 'Stopping billing processes'
    commands.getstatusoutput('/etc/init.d/ebs_core stop')
    commands.getstatusoutput('/etc/init.d/ebs_nf stop')
    commands.getstatusoutput('/etc/init.d/ebs_rad stop')
    commands.getstatusoutput('/etc/init.d/ebs_rpc stop')
    commands.getstatusoutput('/etc/init.d/ebs_nfroutine stop')
    print '*'*80
    print 'Stopping complete'

def start_processes():
    print '*'*80
    print 'Starting billing processes'
    commands.getstatusoutput('/etc/init.d/ebs_core start')
    commands.getstatusoutput('/etc/init.d/ebs_nf start')
    commands.getstatusoutput('/etc/init.d/ebs_rad start')
    commands.getstatusoutput('/etc/init.d/ebs_rpc start')
    commands.getstatusoutput('/etc/init.d/ebs_nfroutine start')
    print '*'*80
    print 'Running complete'

    
def allow_continue(phrase=''):
    a=True
    while a:
        print '*'*80
        if not phrase:
            output = raw_input("\nWe have error. Continue? (y/n)")
        else:
            output = raw_input("\n%s. Continue? (y/n)" % phrase)
        if output in ['n', 'N', 'No', 'Not']:
            sys.exit()
        elif output in ['y', 'Y', 'Yes']:
            a=False
            
def make_archive(name,path):
    return commands.getstatusoutput('tar -cvzf %s.tar.gz %s' % (name, path,))
    
def get_last_sql():
    pass

def pre_upgrade():
    status, output = make_archive('%sdata_%s' % (BACKUP_DIR,curdate), BILLING_PATH)
    if status!=0:
        print "Can not create 'data' backup %s" % output
        allow_continue()
    status, output = make_archive('%swebcab_%s' % (BACKUP_DIR,curdate), WEBCAB_PATH)
    
    if status!=0:
        print "Can not create 'webcab' backup %s" % output
        allow_continue()
    

def files_for_copy():
    to_copy=[]
    for root,dirs,files in os.walk(DIST_PATH):
     
        for f in files:
            to_file = "%s/%s" % (root.replace(DIST_PATH,BILLING_PATH), f)
            from_file = '%s/%s' % (root,f) 
            #print to_file, from_file
            if to_file in exclude_files:continue
            if os.path.exists(to_file):
                if md5gen(from_file)!=md5gen(to_file):
                    #print "%s copy to %s" % (('%s/%s' % (root,f)),"%s/%s" % (root.replace(DIST_PATH,BILLING_PATH), f))
                    to_copy.append((from_file, to_file))
                #else:
                #    print 'DUBLICATE!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!'
            else:
                to_copy.append((from_file, to_file))
    print '\n'.join(["%s->%s" % (x,y) for x,y in  to_copy])
    return to_copy
      
def backup_db():

    print "*"*80  
    print "Please, enter password for DB user %s.\nYou can see right password in file /opt/ebs/data/ebs_config.ini" % (config.get('db', 'username'),)
    status, output = commands.getstatusoutput('pg_dump -W -h %s -p %s -U %s -F p -b -S ebs --disable-triggers -f %s %s' % (config.get('db', 'host'),config.get('db', 'port'),config.get('db', 'username'),"%s%s_db.sql" % (BACKUP_DIR, curdate), config.get('db', 'name')))
    if status!=0:
        print "We have error on database backup operation. %s" % output
        allow_continue()
    print "Backup database completed."
    print "*"*80
        
def upgrade_db():
    print "upgrading DB"
    first_time=False
    if not os.path.exists(LAST_SQL):
        first_time=True
        las_sql_id=0
    

    if not first_time:
        f = open(LAST_SQL, 'r')
        last = f.read()
        f.close()
    
        try:
            las_sql_id = int(last.strip())
        except Exception, e:
            print e
            print "Last SQL id in file %s have incorrect format" % LAST_SQL 
            sys.exit()
    else:
        las_sql_id=0
        
    available_files=[int(x.replace(".sql", '')) for x in os.listdir(SQL_UPGRADE_PATH)]
    
    for id in xrange(las_sql_id+1, max(available_files)+1):
        not_write = False
        upgrade_sql="%s%s.sql" % (SQL_UPGRADE_PATH, id)
        if not os.path.exists(upgrade_sql):
            print "cannot find file %s" % upgrade_sql
            allow_continue('Do you want to continue upgrade of EBS database?')
            continue
            
        sql_file = open(upgrade_sql, 'r')
        sql = sql_file.read()
        sql_file.close()
        
        try:
            cur.execute(sql)
            not_write = False
        except Exception, e:
            conn.rollback()
            print "Error, while importing sql: %s" % sql
            allow_continue('Continue is not recommended. Do you want to continue upgrade of EBS database?')
            not_write=True
            
        if not not_write:
            f = open(LAST_SQL, 'w')
            f.write('%s' % id)
            f.close()
        conn.commit()


def copy_files(files):
    files_copied=[]
    for src, dst in files:
        try:
            shutil.copy(src, dst)
            files_copied.append((src,dst))
        except IOError,e:
            print "I/O Exception %s" % str(e)
            allow_continue()

def post_upgrade():
    pass

def upgrade_from_13():
    print "*"*80
    print "Migrating accounts from 1.3 to 1.4"
    print "*"*80
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    cur.execute("""
    SELECT id, username, "password", fullname, email, address, nas_id, vpn_ip_address, 
           assign_ipn_ip_from_dhcp, ipn_ip_address, ipn_mac_address, ipn_status, 
           status, suspended, created, ballance, credit, disabled_by_limit, 
           balance_blocked, ipn_speed, vpn_speed, ipn_added, city, 
           postcode, region, street, house, house_bulk, entrance, room, 
           vlan, allow_webcab, allow_expresscards, assign_dhcp_null, assign_dhcp_block, 
           allow_vpn_null, allow_vpn_block, passport, passport_date, passport_given, 
           phone_h, phone_m, vpn_ipinuse_id, ipn_ipinuse_id, associate_pptp_ipn_ip, associate_pppoe_mac
      FROM billservice_account;
    """)
    accounts = cur.fetchall()
    
    for account in accounts:
        cur.execute(""" 
        INSERT INTO billservice_subaccount(
                account_id, username, "password", vpn_ip_address, ipn_ip_address, 
                ipn_mac_address, nas_id, ipn_added, ipn_enabled, 
                allow_dhcp, allow_dhcp_with_null, 
                allow_dhcp_with_minus, allow_dhcp_with_block, allow_vpn_with_null, 
                allow_vpn_with_minus, allow_vpn_with_block, associate_pptp_ipn_ip, 
                associate_pppoe_ipn_mac, ipn_speed, vpn_speed, allow_addonservice, 
                vpn_ipinuse_id, ipn_ipinuse_id, allow_ipn_with_null, 
                allow_ipn_with_minus, allow_ipn_with_block)
        VALUES (%s, %s, %s, %s, %s, 
                %s, %s, %s, %s, %s, 
                %s, %s, %s, %s, %s, 
                %s, %s, %s, 
                %s, %s, %s, 
                %s, %s, %s, %s, 
                %s);    
        """, (account['id'],account['username'],account['password'],account['vpn_ip_address'],account['ipn_ip_address'],
              account['ipn_mac_address'],account['nas_id'],account['ipn_added'],account['ipn_status'],
              account['assign_ipn_ip_from_dhcp'],account['assign_dhcp_null'],
              account['assign_dhcp_null'],account['assign_dhcp_block'],account['allow_vpn_null'],
              account['allow_vpn_null'],account['allow_vpn_block'],account['associate_pptp_ipn_ip'],
              account['associate_pppoe_mac'],account['ipn_speed'],account['vpn_speed'],True,
              account['vpn_ipinuse_id'],account['ipn_ipinuse_id'], False, False, False, 
              ))
    
    cur.execute("UPDATE billservice_accountaddonservice as accs SET account_id=Null, subaccount_id=(SELECT id FROM billservice_subaccount  WHERE account_id=accs.account_id LIMIT 1) WHERE accs.deactivated is Null")
    cur.execute("UPDATE billservice_account set nas_id = Null")
    conn.commit()
    print '*'*80
    print "Migration completed"
    
    
def import_dump():
    print "*"*80
    print "Importing main database dump.Enter database password for user %s" % config.get('db', 'username')
    print "*"*80
    status, output = commands.getstatusoutput('psql -W -h %s -p %s -U %s %s -f %s' % (config.get('db', 'host'),config.get('db', 'port'),config.get('db', 'username'), config.get('db', 'name'), DIST_PATH+'/sql/ebs_dump.sql'))
    
    if status!=0:
        allow_continue("We get error when importing initial dump. %s" % output)
        
        
def fromchanges(changes_start=False):
    
    to_db=[]
    
    changes_date = datetime.datetime.now()-datetime.timedelta(days=-1000)
    for line in open(DIST_PATH+'/sql/changes.sql'):
        if line.startswith('--') and not changes_start:
            #print line
            try:
                changes_date = datetime.datetime.strptime(line.strip(), "--%d.%m.%Y")
            except Exception, e:
                print e
                continue
            
        if changes_date>=installation_date:
            changes_start=True
        
        if changes_start==True:
            to_db.append(line)
             
    #print '\n'.join(to_db)   
    try:
        cur.execute('\n'.join(to_db))
        conn.commit()
    except Exception, e:
        print e
    
        #print e 
        #conn.rollback()
    print "*"*80
        #print "Error First stage upgrading DB"
        #allow_continue()
    print 'First stage DB upgrading was completed'
    conn.commit()

if __name__=='__main__':
    installation_date = modification_date(BILLING_PATH+'/license.lic')
    
    if 'install' in sys.argv:
        import_dump()

        fromchanges(changes_start=True)
        upgrade_db()
    if  'upgrade' in sys.argv:
    #print installation_date
        stop_processes()
        pre_upgrade()
        files=files_for_copy()
        if not files:
            print '*'*80
            print 'No files copy needed'
            allow_continue('Do you want to upgrade EBS database?')
    
        copy_files(files)  
        backup_db()
        fromchanges()
        upgrade_db()

    
    
    if 'migrate' in sys.argv:
        allow_continue('Do you want to migrate your accounts database from 1.3 to 1.4 EBS version?')
        backup_db()
        upgrade_db()
        upgrade_from_13()
    
    #start_processes()