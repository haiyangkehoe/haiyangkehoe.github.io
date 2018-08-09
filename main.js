window.onscroll = function() {
  stickyNav(); //Sticky navbar
  scrollColor(); //Change background color
  navScroll(); //Highlight navbar section on scroll
}

//Sticky navbar
var navbar = document.getElementById("navbar");
var sticky = navbar.offsetTop;
function stickyNav() {
  if (window.pageYOffset >= sticky) {
    navbar.classList.add("sticky");
  } else {
    navbar.classList.remove("sticky");
  }
}
     
//Change background color
var header = document.getElementById("header");
var position = 0.4 * header.offsetHeight;
function scrollColor() {
  if (window.pageYOffset >= position) {
    document.body.classList.add("changeColor");
  } else {
    document.body.classList.remove("changeColor");
  }
}

//Highlight navbar section on scroll
var aboutme = document.getElementById("aboutme");
var projects = document.getElementById("projects");
var cv = document.getElementById("cv");
var contact = document.getElementById("contact");
function navScroll() {
  if (window.pageYOffset >= aboutme) {
    navbar.classList.add("active");
  }
}

//Refresh on resize
window.onresize = function() {location.reload()};
