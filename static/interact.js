var websocket;
var name;
var tm;

var i,j;


document.getElementById("menu_marina").onclick= function(){register('M')};
document.getElementById("menu_natasha").onclick=function(){register('N')};
document.getElementById("menu_diana").onclick= function(){register('D')};

function register(nm){
	name=nm;
	websocket = new WebSocket("ws://" + location.host);
	document.getElementById("menu_marina").style.display='none';
	document.getElementById("menu_natasha").style.display='none';
	document.getElementById("menu_diana").style.display='none';
	document.getElementById("menu_text").style.display='none';
	
	
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




