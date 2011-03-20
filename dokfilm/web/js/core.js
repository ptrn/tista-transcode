var annotations = [];
var sliding = false;
var base = '/dokfilm/';
var getKeys = base+'upload/video/getkeys/';

$(document).ready(function() { core.init() });

var core = {
  init: function() {
    $.ajaxSetup({
      'xhr':function() {
        return window.ActiveXObject ? new ActiveXObject("Microsoft.XMLHTTP") : new XMLHttpRequest();
      }
    });

    anno.init();
  },

  getJSON: function(par) {
    par = par || {};

    $.ajax({
      type: 'GET',
      dataType: 'json',
      url: par.url,
      success: function(data){ par.success(data) },
      error: function(XMLHttpRequest, textStatus, errorThrown) {
        par.error(XMLHttpRequest, textStatus, errorThrown);
      }
    });
  },

    timeSplit: function(o) {
        return {
            s: o%60,
            m: Math.floor(o/60)
        }
        // needs hours
    }
}
