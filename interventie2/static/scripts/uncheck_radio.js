function uncheck_radio(groupname) 
{
    var radio_buttons_list = document.getElementsByName(groupname);
    for (var i = 0; i < radio_buttons_list.length; i++) {
        if(radio_buttons_list[i].checked) radio_buttons_list[i].checked = false;
    }
}