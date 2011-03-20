<?php
require_once('../core.php');

header('Content-type: application/json; charset=utf-8');

$policy = new Policy($_GET['fname']);

$a1 = array();
$a2 = array();
$a3 = array();

$a1['name'] = $policy->getBucket();
$a1['uri'] = $policy->getBucketURI();

$a2['key'] = $policy->getFilename();
$a2['acl'] = $policy->getACL();
$a2['content-type'] = $policy->getContentType();
$a2['AWSAccessKeyId'] = $policy->getPublic();
$a2['policy'] = $policy->getPolicy();
$a2['signature'] = $policy->getSignature();
$a2['success_action_redirect'] = $policy->getCallbackURI();

$a3['ext'] = $policy->getExtension();
$a3['original'] = $policy->getFilenameOriginal();

$a = array('meta'=>$a3,'bucket'=>$a1,'fields'=>$a2);

echo json_encode($a);
?>