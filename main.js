// Execute stickyNav and scrollColor on scroll
var navbar = document.querySelector("nav")
var header = document.querySelector("header");

window.onscroll = function() {
    stickyNav(); //Sticky navbar
    scrollColor(); //Change background color
}

// Sticky navbar
function stickyNav() {
    if (window.pageYOffset >= header.offsetHeight) {
        navbar.classList.add("sticky");
    } else {
        navbar.classList.remove("sticky");
    }
}

// Change background color
function scrollColor() {
    if (window.pageYOffset >= 0.44 * header.offsetHeight) {
        document.body.classList.add("changeColor");
    } else {
        document.body.classList.remove("changeColor");
    }
}

// Keep notification active if mouse hovers
let toastTimer;
let hideTimer;

function showToast(message, duration = 8000) {
  const toast = document.getElementById("toast");
  
  // Clear any previous timers
  if (toastTimer) clearTimeout(toastTimer);
  if (hideTimer) clearTimeout(hideTimer);

  toast.innerHTML = message;
  toast.style.display = "block";

  // Make sure toast is fully visible
  toast.classList.remove("hide");

  // After duration, start fade out
  toastTimer = setTimeout(() => {
    toast.classList.add("hide");

    // After fade duration, hide completely
    hideTimer = setTimeout(() => {
      toast.style.display = "none";
    }, 500); // match this to CSS transition duration
  }, duration);

  toast.onmouseenter = () => {
    if (toastTimer) clearTimeout(toastTimer);
    if (hideTimer) clearTimeout(hideTimer);
    toast.classList.remove("hide");
  };

  toast.onmouseleave = () => {
    toastTimer = setTimeout(() => {
      toast.classList.add("hide");
      hideTimer = setTimeout(() => {
        toast.style.display = "none";
      }, 500);
    }, duration);
  };
}

// Copy email
document.querySelectorAll(".mail, .copy-email").forEach(el => {
  el.addEventListener("click", e => {
    e.preventDefault();
    const email = atob(el.dataset.email);

    navigator.clipboard.writeText(email).then(() => {
      showToast(`Email copied to clipboard: <a href="mailto:${email}" style="color:#0b74de;">${email}</a>`);
    });
  });
});
