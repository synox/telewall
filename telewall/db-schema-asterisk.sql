DROP TABLE IF EXISTS "call_history";
CREATE TABLE call_history (
        AcctId INTEGER PRIMARY KEY,
        src varchar(80) NULL default '',
        clid varchar(80) NULL default '',
        start datetime NOT NULL default '0000-00-00 00:00:00',
        end datetime NOT NULL default '0000-00-00 00:00:00',
        dcontext varchar(80) NULL default '',
        channel varchar(80) NULL default '',
        dstchannel varchar(80) NULL default '',
        lastapp varchar(80) NULL default '',
        lastdata varchar(80) NULL default '',
        duration int(11) NULL default '0',
        billsec int(11) NULL default '0',
        disposition varchar(45) NULL default '',
        blocked int(1) NULL default '0',
        sequence int(11) NULL default '0',
        telewall_state varchar(50) NULL default '0',
        uniqueid VARCHAR(32) NULL DEFAULT ''
);
