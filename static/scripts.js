$(document).ready(function() {

    // If user was in a channel then closed browser window, they will be redirected to the last channel
    // alert(window.location.pathname);
    
    // Index page: Add class 'active' to one of the channels in the carousel. Otherwise, carousel won't work.
    $('#singleRecommendedChannel').eq(0).addClass('active');

    // Show all popovers
    $('[data-toggle="popover"]').popover({animation: true});

    // Some alert in login/register route is not available by default, only show when user completed some action
    $('#NotAvailable:empty').hide();
    $('#RegistrationSuccess:empty').hide();

    // configure typeahead
    $("#query").typeahead({
        highlight: false,
        minLength: 1
    },
    {
        display: function(suggestion) { return null; },
        limit: 10,
        source: search,
        templates: {
            suggestion: Handlebars.compile(
                "<div>" +
                "{{ name }}" +
                "</div>"
            )
        }
    });

    /* Click on a suggestion takes user to the book page */
    $("#query").on("typeahead:selected", function(eventObject, suggestion, name) {
        // Construct url to go
        var urlToGo = `/channel/${suggestion.name}`;
        // Redirect to url above
        document.location.href = urlToGo;
    });


    /* Side bar functionalities */
    $('#sidebarCollapse').on('click', function () {
        $('#sidebar').toggleClass('active');
        $(this).toggleClass('active');
    });
    /*=======end side bar=======*/

    /* Carousel in index page functionalities */

    // Control buttons
    $('.next').click(function () {
        $('.carousel').carousel('next');
        return false;
    });
    $('.prev').click(function () {
        $('.carousel').carousel('prev');
        return false;
    });

    // Auto Slide carousel
    $('#carouselExample').on('slide.bs.carousel', function (e) {
        var $e = $(e.relatedTarget);
        var idx = $e.index();
        var itemsPerSlide = 3;
        var totalItems = $('.carousel-item').length;
        
        if (idx >= totalItems-(itemsPerSlide-1)) {
            var it = itemsPerSlide - (totalItems - idx);
            for (var i=0; i<it; i++) {
                // append slides to end
                if (e.direction=="left") {
                    $('.carousel-item').eq(i).appendTo('.carousel-inner');
                }
                else {
                    $('.carousel-item').eq(0).appendTo('.carousel-inner');
                }
            }
        }
    });
    /* ======== End carousel =======*/

    /*==========Filter to search for channel=======*/
    /* This is the standard way but we have to do more as below
    $("#channelSearch").on("keyup", function() {
        var value = $(this).val().toLowerCase();
        $("#channelList .card-title").filter(function() {
            $(this).toggle($(this).text().toLowerCase().indexOf(value) > -1)
        });
    });*/
    $('#channelSearch').on('keyup', function() {
        var input = $(this).val().toLowerCase();
        var cards = $('#channelList .card');
        for (var i = 0; i < cards.length; i++) {
            var title = cards.eq(i).find('.card-title').html().toLowerCase();
            var desc = cards.eq(i).find('.card-text').html().toLowerCase();
            if (title.indexOf(input) > -1 || desc.indexOf(input) > -1) {
                cards.eq(i).parent().show();
            } else {
                cards.eq(i).parent().hide();
            }
        }
    });
    /*========End filter============*/

    /*===========SOCKETIO TO DISPLAY MESSAGE RIGHT AWAY=============*/
    // Connect to websocket. This socket is the page, ANY page that starts with this 
    var socket = io.connect(location.protocol + '//' + document.domain + ':' + location.port);
    //var msg_to_delete;// To mark the to-be-deleted msg, declared first so that variable can be used in many functions below

    // When connected, i.e. the user visits ANY page, configure buttons
    socket.on('connect', function() {
        var room = $('#channel_name').html();// Get the current channel to use as room in Server
        if (room != "") {// If you are in a channel, an actual channel, not other pages
            socket.emit('group users into room', {'room': room});// trigger 'group users into room' in server to add YOU into this room
        }

        // Scroll chatbox to bottom automatically
        $(".msg_history").stop().animate({ scrollTop: $(".msg_history")[0].scrollHeight}, 1000); // Auto scroll to end

        $('.msg_send_btn').on('click', function() {// Click on send chat message
            var msg = $('.write_msg').val();// Get the message
            if (room.includes('sending')) {// meaning user is in PM with someone
                socket.emit('send pm', {'msg': msg, 'room': })
            }
            else {
                socket.emit('send msg', {'msg': msg, 'room': room});// Trigger the 'send msg' route in Server with data as follows
            }
            $('.write_msg').val(''); // Delete the field
            $(".msg_history").stop().animate({ scrollTop: $(".msg_history")[0].scrollHeight}, 1000); // Auto scroll to end of chat box
        });

        // DELETE MESSAGE: THIS IS THE OLD WAY.
        // IN THIS WAY, YOU CAN'T DELETE NEWLY ADDED MSGS BECAUSE THEY ARE NOT BOUND WITH THE 'CLICK' HANDLER
        // BECAUSE YOU APPEND THEM AFTER THE PAGE HAS LOADED (I.E. ONLY ALL THE ELEMENTS LOADED INITIALLY ARE BOUND WITH THE 'CLICK' HANDLER)
        /* $('.msg_history .dropdown-item').each(function(index, value) {
            $(this).on('click', function() {
                // alert($(this).attr('data-deleteid'));
                msg_to_delete = $(this).parents('#saved_msg'); // To know which msg to delete later in socket.on('deleted msg')
                socket.emit('delete msg', {'msg_id': $(this).attr('data-deleteid')});// Send delete msg order to back-end app.py
            });
        });*/

        // DELETE MSG: NEW WAY
        // MORE INFO WHY: https://www.codewall.co.uk/jquery-on-click-function-not-working-after-appending-html/
        // AND https://stackoverflow.com/questions/11375858/append-jquery-values-not-affected-by-javascript
        $('.msg_history').on('click', '.dropdown-item', function(index, value) {
            // alert($(this).attr('data-deleteid'));
            // msg_to_delete = $(this).parents('#saved_msg'); // To know which msg to delete later in socket.on('deleted msg')
            if ($(this).html() == 'Delete this message') {// Only when it's my message, I can't delete others' msgs
                socket.emit('delete msg', {'msg_id': $(this).attr('data-deleteid')});// Send delete msg order to back-end app.py
            }
        });
    });

    socket.on('deleted msg', function(data) {
        // Not working for whole channel because if you dont 'click', you dont have the variable msg_to_delete assigned
        // msg_to_delete.remove();
        $('.msg_history .dropdown-item').each(function(index, value) {
            if ($(this).attr('data-deleteid') == data.deleted_msg_id) {
                // alert($(this).parents('#saved_msg').html());
                $(this).parents('#saved_msg').remove();
            }
            /*$(this).on('click', function() {
                // alert($(this).attr('data-deleteid'));
                msg_to_delete = $(this).parents('#saved_msg'); // To know which msg to delete later in socket.on('deleted msg')
                socket.emit('delete msg', {'msg_id': $(this).attr('data-deleteid')});// Send delete msg order to back-end app.py
            });*/
        });
    });

    socket.on('save client', function(data) {// Receive the order to save client from Server (specifically, from route 'connect')
        localStorage.setItem('client_id', data.client_id);// Save it in localStorage to use it in code below
    })

    // When a new msg is announced, add to the msg history box
    socket.on('announce msg', function(data) {
        // Data received
        var msg_to_add = data.msg;
        var sender_to_add = data.sender;
        var datetime_to_add = data.datetime;
        var sender_id = data.sender_id;
        var msg_id = data.msg_id

        // Content_to_add
        var content_to_add;

        // Problem: If I send the message, it should be on the right side of my screen, and on the left side of others' screens
        if (localStorage.getItem('client_id') != sender_id) {// If I am NOT the sender. Remember, the sender_id is broadcasted by the
                                                            // person who SENDS the message, and thus containing HIS id, not mine.
            // This content will display the message to the left of my screen, because I am not the sender
            content_to_add = '<div class="incoming_msg" id="saved_msg"><div class="incoming_msg_img"><img src="/static/kittylogo.jpg" class="rounded-circle"><p class="text-center">' 
                            + sender_to_add 
                            + '</p></div><div class="received_msg"><div class="received_withd_msg">'
                            + '<div class="dropup"><i class="fas fa-ellipsis-h dropdown-toggle" data-toggle="dropdown"></i><div class="dropdown-menu">'
                            + '<a href="/private" class="dropdown-item" data-deleteid="'
                            + msg_id
                            + '">Send PM</a></div></div><p>'
                            + msg_to_add 
                            + '</p><span class="time_date">' 
                            + datetime_to_add 
                            + '</span></div></div></div>';
        } else {// If I AM the sender
            // This content will display the message to the right of my screen, because I am the sender
            content_to_add = '<div class="outgoing_msg" id="saved_msg"><div class="sent_msg"><div class="dropdown dropleft">'
                            + '<i class="fas fa-ellipsis-h dropdown-toggle" data-toggle="dropdown"></i><div class="dropdown-menu">'
                            + '<a href="#" class="dropdown-item" data-deleteid="'
                            + msg_id
                            + '">Delete this message</a></div></div><p>'
                            + msg_to_add 
                            + '</p><span class="time_date">'
                            + datetime_to_add 
                            + '</span></div></div>';
        }
        
        // Finally, add it to html
        $('.msg_history').append(content_to_add);

        // ...and auto scroll to end, commented out because if you are looking at top of chat box, you don't want to be dragged to end
        $(".msg_history").stop().animate({ scrollTop: $(".msg_history")[0].scrollHeight}, 1000);
    });

    /*============END SOCKET============*/

    /*================AUTO SCROLL CHAT BOX TO BOTTOM=========*/
    /* Already included in SocketIO section
    /*======END AUTO SCROLL CHAT BOX=====*/
});

function search(query, syncResults, asyncResults)
{
    // get books matching query (asynchronously)
    var parameters = {
        q: query
    };
    $.getJSON(Flask.url_for("search"), parameters)
    .done(function(data, textStatus, jqXHR) {
     
        // call typeahead's callback with search results (i.e., places)
        asyncResults(data);
    })
    .fail(function(jqXHR, textStatus, errorThrown) {

        // log error to browser's console
        console.log(errorThrown.toString());

        // call typeahead's callback with no results
        asyncResults([]);
    });
}
