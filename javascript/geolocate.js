var latitude = 0;
var longitude = 0;

function hasClass(ele,cls) {
	return ele.className.match(new RegExp('(\\s|^)'+cls+'(\\s|$)'));
}
function addClass(ele,cls) {
	if (!this.hasClass(ele,cls)) ele.className += " "+cls;
}
function removeClass(ele,cls) {
	if (hasClass(ele,cls)) {
		var reg = new RegExp('(\\s|^)'+cls+'(\\s|$)');
		ele.className=ele.className.replace(reg,' ');
	}
}
function success(position) {
  var s = document.querySelector('#status');
  
  if (s.className == 'success') {
    // not sure why we're hitting this twice in FF, I think it's to do with a cached result coming back    
    return;
  }
  
  s.innerHTML = "found you!";
  s.className = 'success';
  
  var mapcanvas = document.createElement('div');
  mapcanvas.id = 'mapcanvas';
  addClass(mapcanvas,'dialog')

  var useragent = navigator.userAgent;


  if (useragent.indexOf('iPhone') != -1 || useragent.indexOf('Android') != -1 ) {
        mapcanvas.style.width = '100%';
        mapcanvas.style.height = '180px';
  } else {
        mapcanvas.style.width = '600px';
        mapcanvas.style.height = '400px';
  }

    
  document.querySelector('article').appendChild(mapcanvas);
  
  latitude = position.coords.latitude;
  longitude = position.coords.longitude;
  find_events();

  if (google == undefined) {
    alert('google unavailable please try again');
    return;
    }
  var latlng = new google.maps.LatLng(position.coords.latitude, position.coords.longitude);
  var myOptions = {
    zoom: 15,
    center: latlng,
    mapTypeControl: false,
    navigationControlOptions: {style: google.maps.NavigationControlStyle.SMALL},
    mapTypeId: google.maps.MapTypeId.ROADMAP
  };
  var map = new google.maps.Map(document.getElementById("mapcanvas"), myOptions);
  
  var marker = new google.maps.Marker({
      position: latlng, 
      map: map, 
      title:"You are here!"
  });
}

function error(msg) {
  var s = document.querySelector('#status');
  s.innerHTML = typeof msg == 'string' ? msg : "failed";
  s.className = 'fail';
  
  console.log(arguments);
}
function list_refresh() {
  var s = document.querySelector('#found');
  /*s.innerHTML = msg*/
  $('#foundlist').listview();
  $('#foundlist').listview('refresh');

}

  function find_events() {

   var querystring = "";
   if (this.host == undefined)
          querystring = "http://" + this.location.host + "/locations";
   else
          querystring = "http://" + this.host + "/locations";
   var dist=0.1;
   $.ajax({
                    type: "Get",
                    url: querystring ,
                    data: { distance: dist, lon: longitude, lat: latitude},
                    dataType: "json",
                    success: function (response) {
                        var locations = response;
                        var htmlstring = "";
                        if (locations.length == 0) {
                            msg = "<p>no events in your location for today</p>";
                            $('#found').append(msg);
                        }
                        else {
                            $('#foundlist').empty();
                            for (var i=0; i<locations.length; i++) {
                                 var loc = locations[i].location;
                                 var evnt = locations[i].event;
                                 var id = locations[i].key;
                                 var routing = 'checkin/' + id;
                                 msg = "<li><a href='" + routing + "' class='hover_li' title='check into this event' rel='external'> "+evnt+ "@" +loc +"</a></li>";
                                 $('#foundlist').append(msg);
                            }
                            /*list_refresh();*/
                        }
                    },
                    error: function (XMLHttpRequest, textStatus, errorThrown) {
                    // handle error
                    var i=0;
                    },
                    complete: function() {
                            $('#foundlist').listview('refresh');
                            $('#found').page();
        }
    });
   }
$(document).ready( function(){

    $("#locate").click(function (e) {
         find_events();
    });
 });
 

if (navigator.geolocation) {
  navigator.geolocation.getCurrentPosition(success, error, {timeout:10000});
} else {
  alert('geo location not supported');
}