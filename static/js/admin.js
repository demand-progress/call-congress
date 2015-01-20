$(function () {
  var legislatorTemplate = $('#legislatorTemplate').html();

  $.ajax({
    url: '/admin/legislators.json',
    success: function(data) {
      $('select#legislators').empty();
      _.each(data, function(d) {
        $('select#legislators').append(_.template(legislatorTemplate, d));
      });
      $("select#legislators").chosen();
    }
  });

  $('form#campaign').change(function() {
    var form = $('form#campaign').serializeArray();

    // combine repIds
    var repIds = _.where(form, function(d) {
      return d.name == "repIds";
    });
    repIdsList = _.reduce(repIds, function(arr, r) {
      arr.push(r.value);
      return arr;
    }, []);

    // _.object on [name, value] pairs turns to {name: value} hash
    var hash = _.object(_.map(form, function (d) {
      return [d.name, d.value];
    }));

    // replace squashed last elem with full list
    hash['repIds'] = repIdsList;

    var yaml = YAML.stringify(hash);
    $('textarea#yaml').html(yaml);
  });
});