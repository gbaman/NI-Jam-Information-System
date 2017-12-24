var list_of_stuff = [];

window.onload = function(){

        list_of_stuff = $(document.getElementById('current_selected')).data("current-selected").split(",");
        console.log(list_of_stuff);
        var all = document.getElementsByTagName("td");
        for (var i=0;i<all.length;i++) {
            all[i].onclick = inputClickHandler;
        }
        var submit_button = document.getElementById('submit_button');
        submit_button.addEventListener('click', function() {
            data = JSON.stringify(list_of_stuff);
            $.ajax({
                url: '/admin/volunteer_update',
                type: 'POST',
                data: data,
                contentType: 'application/json;charset=UTF-8',
                cache:false,
                success: function (response) {
                    alert("Save completed.");
                    window.location.reload()
                },
                error: function(response){
                    alert('Unable to commit changes. This can be because of a few reasons \n1. You have selected 2 sessions in the same time slot.\n2. You have selected a session that has all the required volunteers.\n3. You have found a bug in the system (very possible), if not sure, check with Andrew.');
                }
            });
        }, false);
    };

    function inputClickHandler(e){
        e = e||window.event;
        var tdElm = e.target||e.srcElement;
        //if(tdElm.style.backgroundColor == 'rgb(255, 0, 0)'){
        if(tdElm.bgColor == '#00bbff'){
            //tdElm.style.backgroundColor = '#fff';
            tdElm.bgColor = '#fff';
            list_of_stuff.splice(list_of_stuff.indexOf(tdElm.id), 1);

        } else {
            if (tdElm.classList.contains("clickable")){
               tdElm.bgColor = '#00bbff';
                list_of_stuff.push(tdElm.id);
            }
            //tdElm.style.backgroundColor = '#f00';

        }
        console.log(list_of_stuff)
    }
