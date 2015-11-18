

function AddDraggableJQuery(){
	// Let all group divs be 'droppable'
    $('.group-div').droppable({
		
      accept: "li.file-select-groups" && function(d) {
	  	//write a fucntion to determine what objects are 'acceptable'
		//we dont want to be able to 'REDROP' elements back in parent		
		if($(d).closest('div').first().attr('name') == $(this).attr('name') )
			return false
		else
			return true
	  },      	  
	  activeClass: "highlight-drop-div",
	  hoverClass:"hover-drop-div",
      drop: function( event, ui ) { 
		$(ui.draggable).appendTo($(this).children('ul'))
      }
    });
	
	//Make all LI elements draggable
	$("li.file-select-groups").draggable({
		placeholder:"ui-state-highlight",
		helper:'clone',
		revert:"invalid"		
	});
}
