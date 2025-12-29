// Sidebar toggle on mobile
const sidebar = document.getElementById("sidebar");
const menuToggle = document.getElementById("menuToggle");

if (menuToggle && sidebar) {
  menuToggle.addEventListener("click", () => {
    sidebar.classList.toggle("open");
  });
}

// Date range dropdown (simple cycle demo)
const dateRangeBtn = document.getElementById("dateRangeBtn");
const dateRangeLabel = document.getElementById("dateRangeLabel");
const dateRanges = ["Today", "This Week", "This Month", "This Quarter", "This Year"];
let dateRangeIndex = 2;

if (dateRangeBtn && dateRangeLabel) {
  dateRangeBtn.addEventListener("click", () => {
    dateRangeIndex = (dateRangeIndex + 1) % dateRanges.length;
    dateRangeLabel.textContent = dateRanges[dateRangeIndex];
  });
}

// Simple fake profile menu click
const profileMenuBtn = document.getElementById("profileMenuBtn");
if (profileMenuBtn) {
  profileMenuBtn.addEventListener("click", () => {
    alert("Profile menu could open here (Settings / Logout etc.).");
  });
}
