var websocket;
var name;
var tm;

var i,j;

function getCookieValue(a) {
    var b = document.cookie.match('(^|;)\\s*' + a + '\\s*=\\s*([^;]+)');
    return b ? b.pop() : '';
}

var room_full=getCookieValue('room_full');
var names_logged_in=getCookieValue(names_logged_in);
var number_of_orphaned_names= getCookieValue('number_of_orphaned_names');
var orphaned_names=[];
for (i=0; i< number_of_orphaned_names; i++){
   orphaned_names.push( getCookieValue(i+"_orphan"));  
}

//Delete all cookies
document.cookie.split(";").forEach(function(c) { document.cookie = c.replace(/^ +/, "").replace(/=.*/, "=;expires=" + new Date().toUTCString() + ";path=/"); });

if (room_full== "True"){
    document.getElementById("name_prompt").innerHTML="Room full";
    document.getElementById("name_input").style.display='none';
    document.getElementById("name_submit_button").style.display='none';
}

if (names_logged_in>=3){
    document.getElementById("name_prompt").style.display='none';
    document.getElementById("name_input").style.display='none';
    document.getElementById("name_submit_button").style.display='none';
}

for (i=0; i<number_of_orphaned_names; i++){
    document.getElementById("orphan_"+i).innerHTML=orphaned_names[i];
    document.getElementById("orphan_"+i).style.display='inline';
    document.getElementById("orphan_"+i).onclick=function(event){
        register(event.target.innerHTML);
        document.getElementById("intro_div").style.display="none";
    }

}


document.getElementById("game_address").innerHTML="http://"+ location.host + location.pathname;

document.getElementById("name_submit_button").onclick=function(){
    var name_entry=document.getElementById("name_input").value;
    if (name_entry != ""){
        register(name_entry);
        document.getElementById("intro_div").style.display="none";
    }
}



function register(nm){
	name=nm;
    websocket = new WebSocket("ws://" + location.host+ location.pathname);
	
	websocket.onopen = function(){
		send_message_to_server({name: nm});
		setInterval(ping, 3000);
	}
	
	websocket.onmessage = function (event) {
        data = JSON.parse(event.data);
        respond_to_message(data);
	}
}

function ping() {
	if (websocket.readyState === WebSocket.OPEN){
        send_message_to_server({type: "__ping__"});
        tm = setTimeout(function () {
           websocket.close();
           register(name);
		}, 4000);
	}
	else if(websocket.readyState === WebSocket.CLOSED){
		register(name);
	}
		
}

function pong(){
	clearTimeout(tm);
}

function send_message_to_server(args){
	websocket.send(JSON.stringify(args));
}



function respond_to_message(args){
	
	switch (args.type){
		case 'error':
			alert("error: " + args.msg);
			break;
		case 'debug':
			alert( "debug: " + args.msg);
			break;
		case '__pong__':
			pong();
			break;
		case 'refresh':
			refresh(args);
			break;
		case 'users':
			update_users(args);
			break;
		case 'alert':
			alert(args.msg);
			break;
		case 'deemph':
			deemph_all(); // lower the divs corresponding to players' cards
			break;	
		case 'show_score':
			show_score();
			break;
	}
	
	
}



function send_turn_data(){
	
	send_message_to_server({type:"turn_data", data:turn_data});
}

