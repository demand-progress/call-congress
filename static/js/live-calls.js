// simple param extract from location
function getQueryVariable(variable) {
       var query = window.location.search.substring(1);
       var vars = query.split("&");
       for (var i=0;i<vars.length;i++) {
               var pair = vars[i].split("=");
               if(pair[0] == variable){return pair[1];}
       }
       return(false);
}

function getRecentCalls() {
  $.ajax({
    url: '/recent_calls.json',
    data: { campaign: campaign,
            since: lastRun,
            limit: '25'
    },
    success: function(data) {
      console.log('callback @ '+lastRun, data);
      var t = callsTemplate({calls: data.calls});
      $('ul#calls').prepend(t);
      $("abbr.timeago").timeago();
      lastRun = (new Date()).toISOString();
    }
  });
}

var lastRun, callsTemplate, campaign, interval;
$(function () {
  campaign = getQueryVariable('campaign');
  headerTemplate = $('#header').html();
  $('h1#campaign').html(
    _.template(headerTemplate, {campaign: campaign})
  );

  callsTemplate = _.template($('#recent-calls-template').html());

  var since = getQueryVariable('since');
  if (since) { lastRun = since; }
  else { lastRun = new Date(((new Date()) - 24*60*1000)).toISOString(); } // default to last 24 hours

  getRecentCalls();
  interval = setInterval(getRecentCalls, 60*1000); // refresh once per minute
});