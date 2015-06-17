# modifying settings #

All examples shown here are done with the following settings:

  * base path set to `/dokfilm/prototype/ajax/`
  * Amazon S3 bucket is `dokfilm-raw_up`

## change path in filedirectory ##

As no files in the system are absolute, one can change the internal path without having to change any settings.

## change path in URI ##

If you want to move the site root from one path to another on the server, you will have to change the base path defined in the [.htaccess](webFilestructure#.htaccess.md) file, as well as a variable in [core.php](webFilestructure#core.php.md).

`.htaccess`:
```
RewriteBase /dokfilm/prototype/ajax/
```

`core.php`:
```
$GLOBALS['CONF']['path'] = '/dokfilm/prototype/ajax/';
```

However, changing domain or subdomain does not require any changes of settings.

## change Amazon S3 bucket ##

If changing the Amazon S3 bucket, the following changes will have to be done:

`core.php`:
```
$GLOBALS['CONF']['s3']['bucket'] = 'dokfilm-raw_up';
$GLOBALS['CONF']['s3']['bucketURI'] = 'http://s3.amazonaws.com/dokfilm-raw_up';
```

## change Amazon access keys ##

Getting new access keys can be done by loggin in to the Amazon Web Services panel, and then selecting Security Credentials. Generating new access keys will give new values on both the public and private key.

The following changes will have to be done:
`core.php`
```
$GLOBALS['CONF']['s3']['public'] = '1234567890abc';
$GLOBALS['CONF']['s3']['private'] = 'abc+def+ghi';
```

## change Amazon account ##

Changing the Amazon account will trigger a access key change, and unless the bucket used previously is transferred the bucket will also need to be changed.

See [changing Amazon access keys](webSettings#change_Amazon_access_keys.md) and [changing Amazon S3 bucket](webSettings#change_Amazon_S3_bucket.md).

```
$GLOBALS['CONF']['s3']['bucket'] = 'dokfilm-raw_up';
$GLOBALS['CONF']['s3']['bucketURI'] = 'http://s3.amazonaws.com/dokfilm-raw_up';
```

## change transcoding formats ##

Currently the predefined output formats include MP4 (h.264+ACC) and OGG(Theora+Vorbis). To modify, remove or add output formats you must enter a new array of parameters in the formats array, as defined in `core.php`.

```
$GLOBALS['CONF']['ttc']['output'] = array(
                               array(
                                     'format'=>'mp4',
                                     'vcodec'=>'h.264',
                                     'acodec'=>'aac',
                                     'vbitrate'=>1024,
                                     'abitrate'=>128,
                                     'width'=>640,
                                     ),
                               array(
                                     'format'=>'ogg',
                                     'vcodec'=>'theora',
                                     'acodec'=>'vorbis',
                                     'vbitrate'=>1024,
                                     'abitrate'=>64,
                                     'width'=>640,
                                     ),
                               );
```

Allowed parameters is defined under [TTC interface](TTC#Add_one_job.md). Note that not all allowed parameters are shown in the example above.