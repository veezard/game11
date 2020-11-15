var card_height=document.getElementById("C0").clientHeight;
var card_height=document.getElementById("C0").clientWidth;


class Card {
	constructor(suit, number){
		this.suit = suit;
		this.number = number;
	}
	get card_file(){
		if (this.suit== null){
			return "url('img/back.png')";
		}
		else {
			return "url('img/cards/"+ this.number + this.suit + ".png')";
		}
	}
}
 
function create_gameplay_divs(){
	var i; 
	var newDiv;
	var game_play_div = document.getElementById("game_play");
	for (i=0; i<52 ; i++){
		
		newDiv = document.createElement("div");
		newDiv.classList.add('card');
		newDiv.id = "play_card_" + i +"_";
		newDiv.style.display = "none";
		if (i< 24){
			newDiv.style.transform = "translate(" +(-175 + 70* (i%6)) +"pt," + Math.floor(i/6) * 105 + "pt)";
		} else if (i<40) {
			if ( (i%2) ==0){
				newDiv.style.transform = "translate(" +(- 245 -  70 *Math.floor((i-24)/8))+ "pt, " +105 * (Math.floor((i-24)/2)  % 4)  + "pt)"; 
			} else{
				newDiv.style.transform = "translate(" + (245 +  70 *Math.floor((i-25)/8))+ "pt, " +105 * (Math.floor((i-25)/2)  % 4)  + "pt)"; 
			}
		} else{
			newDiv.style.transform = "translate(" +(-315  +  70 * (i-40)) + "pt, " +420  + "pt)"; 
		}
		game_play_div.appendChild(newDiv);
		
	}
	
	
}

function create_all_cards(){
	var i,j;
	var dict = {
		0: "S",
		1: "C",
		2: "H",
		3: "D"
	};
	var cards=new Array(5);
	
	for(i=0;i<4; i++){
		cards[i]=[]
		for(j=0; j<13; j++){
			cards[i].push(new Card(dict[i],j+1));
		}
	}
	cards[4]= new Card(null,null);
	return cards;
	
}

var players=["L", "C", "R"];
var l_cards = [null,null,null,null];
var r_cards = [null,null,null,null];
var c_cards = [null,null,null,null];
var t_cards = new Array(52);
t_cards.fill(null,0,52);

var score={"D":0,"M":0, "N":0};
var last_round_score ={"D":0,"M":0, "N":0};

var last_round_hands={"D":[],"M":[], "N":[]};


var num_to_name= {0:"D", 1:"M", 2:"N" };
var name_to_num= {"D":0, "M":1, "N":2 };
var players_to_positions={0:"C", 1:"L", 2:"R"};


create_gameplay_divs();
cards= create_all_cards();
create_score_card_divs();

var turn= -1;
var dealer= -1;
var turn_data={c_card_selected:-1, t_cards_selected : Array(52).fill(0)};
var deck_size=0;
var pile_sizes=[0,0,0];
var pile_ends=[[],[],[]];

var can_undo = false;


function create_score_card_divs(){
	
		for (i=0; i<3 ; i++){
			score_div= document.getElementById( num_to_name[i] + "_last_round");
			for (j=0; j< 52 ; j++){
				newDiv = document.createElement("div");
				newDiv.classList.add('card');
				newDiv.id="last_round_score_card_" +i + "_" + j + "_";
				newDiv.style.transform = "translate(" +(90+ j* 13) + "pt, 0pt)";
				newDiv.style.display="none";
				score_div.appendChild(newDiv);
			}
		
		}

	
}





function server_card_to_js_card(server_card){
	// (-1,-1) encodes lack of a card and (-2,-2) encodes card face down
	if (server_card[0]==-1){
		return null;
	}
	else if (server_card[0]==-2){
		return cards[4];
	}
	else{
		return cards[server_card[0]][server_card[1]];
	}

}
function refresh(args){
	
	for(i=0; i<4; i++){
		c_cards[i] = server_card_to_js_card(args.c_player[i]);
	}
	for(i=0; i<4; i++){
		l_cards[i] = server_card_to_js_card(args.l_player[i]);
	}
	for(i=0; i<4; i++){
		r_cards[i] = server_card_to_js_card(args.r_player[i]);
	}
	for(i=0; i<52; i++){
		t_cards[i] = server_card_to_js_card(args.table_cards[i]);
	}
	
	// update last round hands 
	for (i=0; i<3; i++){
		last_round_hands[num_to_name[i]]=[];
	}
	
	var last_round_cards;
	for(i=0; i<3; i++){
		last_round_cards=args.last_round_hands[num_to_name[i]];
		for (j=0;j < last_round_cards.length; j++){
			last_round_hands[num_to_name[i]].push(cards[last_round_cards[j][0]][last_round_cards[j][1]]);
			
		}
		
	}
	
	
	
	turn = args.turn;
	dealer= args.dealer;
	turn_data.c_card_selected=args.turn_data.player_card_selected;
	turn_data.t_cards_selected=args.turn_data.t_cards_selected;
	deck_size=args.deck_size;
	pile_sizes=args.pile_sizes;
	pile_ends=args.pile_ends;
	score=args.score;
	last_round_score=args.last_round_score;
	
	can_undo=args.can_undo;
	
	display_update();
	
}
function display_update(){
	var i;
	var card_dom;
	// update Lplayer
	for (i=0; i< 4 ; i++){
		if (l_cards[i]== null){
			document.getElementById("L"+i).style.display = "none";
		}
		else {
			
			card_dom=document.getElementById("L"+i);
			card_dom.style.backgroundImage=l_cards[i].card_file;
			card_dom.style.display= "inline";
		}
	}
	// update Rplayer
	for (i=0; i< 4 ; i++){
		if (r_cards[i]== null){
			document.getElementById("R"+i).style.display = "none";
		}
		else {
			card_dom=document.getElementById("R"+i);
			card_dom.style.backgroundImage=r_cards[i].card_file;
			card_dom.style.display= "inline";
		}
	}
	
	// update Cplayer
	for (i=0; i< 4 ; i++){
		if (c_cards[i]== null){
			document.getElementById("C"+i).style.display = "none";
		}
		else {
			card_dom=document.getElementById("C"+i);
			card_dom.style.backgroundImage=c_cards[i].card_file;
			card_dom.style.display= "inline";
		}
	}	
	
	// update table cards
	var len = t_cards.length;
	for (i=0; i < len ; i++){
		if (t_cards[i]== null){
			document.getElementById("play_card_"+i+"_").style.display = "none";
		}
		else{
			card_dom=document.getElementById("play_card_"+i+"_");
			card_dom.style.backgroundImage=t_cards[i].card_file;
			card_dom.style.display= "inline";
		}
		
	}
	// display play button
	if (turn ==0){
		document.getElementById("play_button").style.display=("inline");
	}
	else {
		document.getElementById("play_button").style.display=("none");
	}
	 
	move_spotlight(turn);
	move_dealer(dealer);
	
	// color table cards
	
	var i;
	for (i=0; i<52; i++){
		if (turn_data.t_cards_selected[i]==1){
			table_card_emph(document.getElementById("play_card_"+i+"_"));
		}
		else {
			table_card_deemph(document.getElementById("play_card_"+i+"_"));
		}	
	}
	
	
	deemph_all(); // lower all cards
	
	
	// raise/lower selected player card
	var turn_player_position, i ;
	switch (turn){	
		case 0:
			turn_player_position="C";
			break;
		case 1:
			turn_player_position="L";
			break;
		case 2:
			turn_player_position="R";
			break;
	}
	for (i=0;i<4; i++){
		if (turn_data.c_card_selected!=i){
			player_card_deemph(document.getElementById(turn_player_position + i));
		}
		else{
			player_card_emph(document.getElementById(turn_player_position + i));
		}	
	}
	
	// change deck size
	if (deck_size==0){
		document.getElementById("deck").style.display="none";
	}
	else{
		deck_elm=document.getElementById("deck");
		deck_elm.style.display="inline";
		
		deck_elm.children[0].style.boxShadow =  parseInt(deck_size/3) + "pt 0pt 0  rgba(0, 0, 0,0.5)";
	}
	
	// change pile sizes
	
	for(i=0; i<3 ; i++){
		if (pile_sizes[i]==0){
			document.getElementById(i+"pile").style.display="none";
		}
		else{
			pile_elm=document.getElementById(i+"pile");
			pile_elm.style.display="inline";
			pile_elm.style.boxShadow = "0 "+ Math.ceil(pile_sizes[i]/3) + "pt 0  rgba(0, 0, 0,0.5)";
		
		}
	
		
	}
	
	
	// display score	
	for(i=0; i<3 ; i++){
		document.getElementById( num_to_name[i]+"_score").innerHTML= score[num_to_name[i]];
		document.getElementById( num_to_name[i]+"_last_round_score").innerHTML= last_round_score[num_to_name[i]];
	}
	show_last_round();
	
	// show or hide undo button 
	if (can_undo){
		document.getElementById("undo_button").style.display="inline";
	}
	else {
		document.getElementById("undo_button").style.display="none";
	
	}
}

function update_users(args){
	var name_to_file = {'M':"marina", "N": "natasha", "D": "diana"};
	document.getElementById("Lavatar").style.backgroundImage="url('img/"+ name_to_file[args.l_user] + ".jpg')";
	document.getElementById("Ravatar").style.backgroundImage="url('img/"+ name_to_file[args.r_user] + ".jpg')";
}

function move_spotlight(user){
	var dim_in=document.getElementById("dim_in");
	var dim_out= document.getElementById("dim_out");
	if (user==0){
		dim_in.style.left= "240pt";
		dim_in.style.right="240pt";
		dim_in.style.bottom= "0pt";
		dim_in.style.top="80pt";
		
		dim_out.style.left= "240pt";
		dim_out.style.right="240pt";
		dim_out.style.bottom= "0pt";
		dim_out.style.top="80pt";
	}
	else if (user == 1){
		dim_in.style.left= "0pt";
		dim_in.style.right="240pt";
		dim_in.style.bottom= "120pt";
		dim_in.style.top="80pt";
		
		dim_out.style.left= "0pt";
		dim_out.style.right="240pt";
		dim_out.style.bottom= "120pt";
		dim_out.style.top="80pt";
	}
	else if (user ==2){
		dim_in.style.left= "240pt";
		dim_in.style.right="0pt";
		dim_in.style.bottom= "120pt";
		dim_in.style.top="80pt";
		
		dim_out.style.left= "240pt";
		dim_out.style.right="0pt";
		dim_out.style.bottom= "120pt";
		dim_out.style.top="80pt";
		
	}
	
}

function move_dealer(dealer){
	
	var dealer_dom=document.getElementById("dealer");
	
	switch(dealer){
		case 0:
			
			document.getElementById("playerC").appendChild(dealer_dom);
			dealer_dom.style.transform="translate(-200pt,-20pt)";
			
			break;
		case 1:
			
			document.getElementById("playerL").appendChild(dealer_dom);
			dealer_dom.style.transform="translate(-220pt,-110pt) rotate(-90deg)";
			break;
		case 2:
			document.getElementById("playerR").appendChild(dealer_dom);
			dealer_dom.style.transform="translate(180pt,-110pt) rotate(90deg)";
			break;
	}
}

function player_card_emph(card_element){

	var player= card_element.id[0];
	document.getElementById("player" + player +"_lifted").appendChild(card_element);
	
	card_element.style.boxShadow =" 0 20pt 0  rgba(0, 0, 0,0.5)";
	
}

function player_card_deemph(card_element){

	var player= card_element.id[0];
	document.getElementById("player" + player).appendChild(card_element);
	card_element.style.boxShadow =" 0 0 0  rgba(0, 0, 0,0.5)";
}


function table_card_emph(card_element){
	
	card_element.style.boxShadow ="inset 0 0 0 100pt rgba(4, 181, 52 , 0.3)";
}

function table_card_deemph(card_element){
	
	card_element.style.boxShadow ="";
}


function deemph_all(){
	
	var i,j;
	var players_to_positions={0:"C", 1:"L", 2:"R"};
	for (i=0;i<3; i++){
		for (j=0; j<4; j++){
		player_card_deemph(document.getElementById(	players_to_positions[i] + j));	
		}	
	}
	
}


function show_last_round(){
	var last_round_cards;
	for (i=0; i<3 ; i++){
		last_round_cards=last_round_hands[num_to_name[i]];
		for (j=0; j< 52; j++){
			card_div=document.getElementById("last_round_score_card_" +i + "_" + j + "_");
			if (j< last_round_cards.length){
				card_div.style.backgroundImage=last_round_cards[j].card_file;
				card_div.style.display="inline";
			}
			else {
				card_div.style.backgroundImage="";
				card_div.style.display="none";
			}
			
		}
		
	}
}



