
for (i=0 ; i<4 ; i++){
	document.getElementById("C"+i).onclick= c_card_click;
}
document.getElementById("play_button").onclick=play_button_click;
document.getElementById("undo_button").onclick=function(){
	send_message_to_server({type:"undo"});
	
	}
document.body.onkeyup = function(e){
    if(e.keyCode == 32){
        play_button_click()
    }
}
document.getElementById("score_button").onclick=score_button_click;
document.getElementById("rules_button").onclick=rules_button_click;

document.getElementById("dealer").onclick= function(){
	
	send_message_to_server({type:"deal"});
}

for (i=0 ; i<3 ; i++){
	document.getElementById(i+ "pile").onclick= pile_click;
}


for (i=0; i<52 ; i++){
	document.getElementById("play_card_" + i +"_").onclick= table_card_click;
}

function c_card_click(event){
	if (turn !=0){
		return;
	}
	if (c_cards[event.target.id[1]]==null){
		return;
	}
	if (event.target.id[1]== turn_data.c_card_selected){
		player_card_deemph(event.target);
		turn_data.c_card_selected=-1;
	}
	else{
		player_card_emph(event.target);
		if (turn_data.c_card_selected != -1){
			player_card_deemph(document.getElementById("C"+turn_data.c_card_selected));
		}
		turn_data.c_card_selected=parseInt(event.target.id[1]);
	} 
	send_turn_data();
}



function play_button_click(event){
	
	if (turn !=0){
		return;
	}
	send_message_to_server({type:"play_hand"});	
}

function pile_click(event){
		player_number = event.target.id[0];
		
		for (i=0; i<pile_ends[player_number].length; i++){
			
			card= cards[pile_ends[player_number][i][0]][pile_ends[player_number][i][1]]
			newDiv = document.createElement("div");
			newDiv.classList.add('card');
			newDiv.style.transform = "translate(" + (200 - 400* (Math.floor(player_number/2) %2) + i*13) + "pt, 0pt)"; // for player=2, we need to translate by -200 instead of 200
			newDiv.style.display="inline";
			newDiv.id="card" + i ;
			newDiv.style.backgroundImage=card.card_file;
			event.target.parentElement.appendChild(newDiv);
			setTimeout( function(elm){elm.remove();},2000, newDiv);
			
		}
}




function table_card_id_to_number(table_card_id){
	if (table_card_id[11]=="_"){
		return table_card_id[10];
	}
	else {
		return parseInt(table_card_id.slice(10,12));
	}
}

function table_card_click(event){
	if (turn !=0){
		return;
	}
	var table_card_number= table_card_id_to_number(event.target.id);
	if (t_cards[table_card_number]==null){
		return;
	}
	if (turn_data.t_cards_selected[table_card_number] ==0){
		table_card_emph(event.target);
		turn_data.t_cards_selected[table_card_number] =1;
	}
	else {
		table_card_deemph(event.target);
		turn_data.t_cards_selected[table_card_number] =0;
	}
	send_turn_data();
	
}

function show_score(){
	score_div=document.getElementById("score_board");
	score_div.style.display = "inline";
	show_last_round();
	
}

function score_button_click(){
	score_div=document.getElementById("score_board");
	if (score_div.style.display == "none") {
		score_div.style.display = "inline";
	} else {
		score_div.style.display = "none";
	}
}
function rules_button_click(){
	rules_div=document.getElementById("rules_window");
	if (rules_div.style.display == "none") {
		rules_div.style.display = "inline";
	} else {
		rules_div.style.display = "none";
	}
}
