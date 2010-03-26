-- Remove old version
drop table Jobs cascade;
drop table Parameters;
drop function RandomHexString(int);

-- Create hex-encoded random strings of arbitrary length.
create function RandomHexString(int)
returns char as
'import ttc.model; return ttc.model.RandomHexString(args[0])'
language plpythonu;

-- Job states:
--   w: waiting
--   i: in progress
--   f: finished
--   e: erroneous

create table Jobs (
  id char(32)  primary key default RandomHexString(32),
  creationTime timestamp with time zone not null default current_timestamp, -- When job was submitted
  srcURI varchar(512),
  dstURI varchar(512) unique, -- Destination path (file:///...)

  priority int not null check (priority > 0),
  srcSize bigint,
  state char(1) check(state = 'w' or state = 'i' or state = 'f' or state = 'e') not null default 'w',

  workerAddress inet,
  workerStartTime timestamp with time zone,
  workerHeardFrom timestamp with time zone,
  workerRelativeProgress int, -- percent
  workerLog varchar(8192)

  -- check (state = 'w' or (workerAddress is not null and workerStartTime is not null))
);

create table Parameters (
  jobID  char(32) references Jobs on delete cascade,
  key varchar(32),
  value varchar(32)
);

-- Permissions
grant insert, select, update on Jobs to "www-data";
grant insert, select, update on Parameters to "www-data";
grant insert, select, update on Jobs to "tord";
grant insert, select, update on Parameters to "tord";
