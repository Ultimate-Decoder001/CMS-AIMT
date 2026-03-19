// Custom JS: tooltips, counters, small UI interactions
console.log('AIMT custom.js loaded');
document.addEventListener('DOMContentLoaded', function(){
    // Bootstrap tooltips
    try {
        var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
        tooltipTriggerList.forEach(function (el) { new bootstrap.Tooltip(el) })
    } catch(e){}

    // Animate numeric counters
    function animateCounter(el, end) {
        var start = 0;
        var duration = 800;
        var range = end - start;
        var startTime = null;
        function step(timestamp) {
            if (!startTime) startTime = timestamp;
            var progress = Math.min((timestamp - startTime) / duration, 1);
            el.textContent = Math.floor(progress * range + start);
            if (progress < 1) {
                window.requestAnimationFrame(step);
            } else {
                el.textContent = end;
            }
        }
        window.requestAnimationFrame(step);
    }

    document.querySelectorAll('.counter').forEach(function(span){
        var val = parseInt(span.getAttribute('data-count')||0,10);
        animateCounter(span, val);
    });

    // Notification toggle (placeholder)
    var notifToggle = document.getElementById('notifToggle');
    if (notifToggle) {
        notifToggle.addEventListener('click', function(e){ e.preventDefault(); alert('No new notifications (demo).'); });
    }

    // Sidebar submenu toggle
    document.querySelectorAll('.has-submenu').forEach(function(btn){
        btn.addEventListener('click', function(e){
            e.preventDefault();
            console.log('submenu toggle clicked for', btn.textContent.trim());
            var submenu = btn.nextElementSibling;
            if (submenu && submenu.classList.contains('submenu')) {
                var isOpen = submenu.classList.toggle('show');
                btn.setAttribute('aria-expanded', isOpen ? 'true' : 'false');

                var icon = btn.querySelector('.fa-chevron-down');
                if (icon) icon.classList.toggle('rotate-180');
            }
        });
        // Provide semantic hint for keyboard users
        btn.setAttribute('role', 'button');
        btn.setAttribute('aria-expanded', 'false');
    });
});
