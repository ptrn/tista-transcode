-- Create hex-encoded random strings of arbitrary length.
create function RandomHexString(int)
returns char as
'import ttc.model; return ttc.model.RandomHexString(args[0])'
language plpythonu;

-- Job states:
--   f: finished
--   i: in progress
--   w: waiting
create table Jobs (
  id char(32)  primary key default RandomHexString(32),
  creationTime timestamp with time zone not null default current_timestamp, -- When job was submitted
  dstPath varchar(512) unique, -- Destination path (file:///...)
  recipe varchar(64) not null,
  priority int not null check (priority > 0),
  srcSize bigint,
  state char(1) check(state = 'f' or state = 'i' or state = 'w') not null default 'w',

  workerAddress inet,
  workerStartTime timestamp with time zone,
  workerHeardFrom timestamp with time zone,
  workerRelativeProgress int -- percent

  -- check (state = 'w' or (workerAddress is not null and workerStartTime is not null))
);

-- Jobs may involve more than one source file (e.g. when files have
-- been split due to size limits).
create table SourcePaths (
  jobID char(32) references Jobs on delete cascade,
  path varchar(512),
  primary key(jobID, path)
); 

-- Permissions
grant select, update on Jobs to "www-data";
grant select, update on SourcePaths to "www-data";

-- New structure
create table Jobs2 (
  id char(32)  primary key default RandomHexString(32),
  creationTime timestamp with time zone not null default current_timestamp, -- When job was submitted
  srcURI varchar(512),
  dstURI varchar(512) unique, -- Destination path (file:///...)

  priority int not null check (priority > 0),
  srcSize bigint,
  state char(1) check(state = 'f' or state = 'i' or state = 'w') not null default 'w',

  workerAddress inet,
  workerStartTime timestamp with time zone,
  workerHeardFrom timestamp with time zone,
  workerRelativeProgress int, -- percent
  workerLog varchar(8192)

  -- check (state = 'w' or (workerAddress is not null and workerStartTime is not null))
);

create table Parameters (
  jobID  char(32) references Jobs2 on delete cascade,
  key varchar(32),
  value varchar(32)
);

-- Permissions
grant insert, select, update on Jobs2 to "www-data";
grant insert, select, update on Parameters to "www-data";
