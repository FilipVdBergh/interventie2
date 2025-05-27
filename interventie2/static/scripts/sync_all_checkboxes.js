function sync_all_checkboxes() 
{
    var master_checkbox = document.getElementById('sync_all')
    var all_instruments = document.getElementsByClassName('checkbox')
    for (var i = 0; i < all_instruments.length; i++) {
        all_instruments[i].checked = master_checkbox.checked
    }
}