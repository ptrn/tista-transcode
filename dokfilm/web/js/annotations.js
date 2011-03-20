var anno = {
  data: null,

  init: function() {
    if ($('#vid').length == 0) return;

    this.data = annotations;
    this.draw();

    setInterval('anno.updateTime()',100);
  },

  durationChanged: function() {
    //$('#vid').on
    //$('#time-from')
    var vid = $('#vid')[0];
    var dur = Math.round(vid.duration);

    var durArr = core.timeSplit(dur);

    console.log(durArr);

    var s = (durArr.m > 0 || durArr.s == 59 ? 59 : durArr.s);

    // to
    $('#time-from').append('from: ');
    var p = $('<select name="from-m"></select>')
    for (var i=0; i<=durArr.m; i++)
      p.append('<option>'+i+'</option>');
    $('#time-from').append(p);
    $('#time-from').append(':');
    var p = $('<select name="from-s"></select>')
    for (var i=0; i<=s; i++)
      p.append('<option>'+i+'</option>');
    $('#time-from').append(p);

    // to
    $('#time-from').append('to: ');
    var p = $('<select name="to-m"></select>')
    for (var i=0; i<=durArr.m; i++)
      p.append('<option>'+i+'</option>');
    $('#time-from').append(p);
    $('#time-from').append(':');
    var p = $('<select name="to-s"></select>')
    for (var i=0; i<=s; i++)
      p.append('<option>'+i+'</option>');
    $('#time-from').append(p);
  },

  draw: function() {
    var par = $('#movie_annot');

    if (this.data.length==0) {
      // no annot's
      par.append('no annotations');
    }
    else {
      var tmp = $('<table></table>');

      for (var i=0; i<this.data.length; i++) {
        var tr = $('<tr class="annotationRow" id="annotation-id-'+i+'"></tr>');
        tr.append('<td class="annotation">'+this.formatTime(this.data[i].timeStart)+' - '+this.formatTime(this.data[i].timeEnd)+'</td>');
        tr.append('<td class="annotation">'+this.data[i].content+'</td>');
        tmp.append(tr);
      }
      par.append(tmp);
    }
  },

  updateTime: function() {
    var c = $('#vid')[0].currentTime*1000;
    var o = anno.data;

    //console.log('time: '+c);

    for (var i=0; i<o.length; i++) {
      if (o[i].timeStart<c && o[i].timeEnd>c) {
        var b = $('#annotation-id-'+i).css('background-color');
        if (b=='transparent' || b=='rgba(0, 0, 0, 0)') {
          $('#annotation-id-'+i).css('background-color','red');
        }
      }
      else {
        if ($('#annotation-id-'+i).css('background-color')!='transparent') {
          $('#annotation-id-'+i).css('background-color','transparent');
        }
      }
    }



    // parse and mark active annotations
  },

  formatTime: function(t) {
    t = (t/1000).toFixed(1);

    var s = (t%60).toFixed(1);
    var m = Math.floor((t%3600)/60);
    var h = Math.floor(t/3600);
    
    var r = '';
    // if  hours
    if (h!=0) r += h+':';
    r += +m+':'+s;
    return r;
  }
};
