var console;

$(document).ready(function() {
  upload.init();
});

var upload = {
  isClicked: false,
  isReady: false,
  preEvent: null,

  init: function() {
    // creating console object for browsers not running Firebug
    if (console==null) {
      console = {};
      console.log = function() { return };
      console.info = function() { return };
      console.error = function() { return };
    }
  },

  click: function() {
    console.log('triggered, ready: '+(upload.isReady?'yes':'no'));
    if (upload.isReady) $('#uploadForm').submit();
    if (upload.isClicked) return;
    upload.pre();
  },

  pre: function() {
    upload.isReady = false;
    var file = $('#uploadFile').val();

    if (file.length==0) return false;

    core.getJSON({
      url:getKeys+file,
      success: function(data) {
        var fields = data.fields;
        var form = $('#uploadForm');

        form.attr('action',data.bucket.uri);

        for (key in fields) {
          var children = form.children();

          if (false)
            $(children[0]).before('<span>'+key+'</span> <input style="width: 100%" name="'+key+'" type="text" value="'+fields[key]+'" />');
          else 
            $(children[0]).before('<input name="'+key+'" type="hidden" value="'+fields[key]+'" />');
        }

        console.log('res is in');

        upload.isReady = true;
        form.submit();
      },
      error: function() { console.info('error') }
    });
  }
}
